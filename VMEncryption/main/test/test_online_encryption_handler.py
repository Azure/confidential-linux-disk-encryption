#!/usr/bin/env python

import unittest
import sys
import os
import uuid
import threading
from unittest.mock import Mock, patch, MagicMock, call
try:
    from queue import Queue, Empty # Python 3
except ImportError:
    from Queue import Queue, Empty # Python 2

# Add the parent directory to the path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from OnlineEncryptionHandler import OnlineEncryptionHandler, OnlineEncryptionItem
from Common import CommonVariables, CryptItem, DeviceItem


class TestOnlineEncryptionItem(unittest.TestCase):
    
    def test_init(self):
        """Test OnlineEncryptionItem initialization"""
        crypt_item = CryptItem()
        bek_file_path = "/path/to/bek"
        
        item = OnlineEncryptionItem(crypt_item, bek_file_path)
        
        self.assertEqual(item.crypt_item, crypt_item)
        self.assertEqual(item.bek_file_path, bek_file_path)


class TestOnlineEncryptionHandler(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_logger = Mock()
        self.security_type = CommonVariables.StandardVM
        self.public_setting = {"test": "value"}
        
        self.handler = OnlineEncryptionHandler(
            self.mock_logger, 
            self.security_type, 
            self.public_setting
        )

    def test_init(self):
        """Test OnlineEncryptionHandler initialization"""
        self.assertIsInstance(self.handler.devices, Queue)
        self.assertEqual(self.handler.logger, self.mock_logger)
        self.assertEqual(self.handler.security_type, self.security_type)
        self.assertEqual(self.handler.public_setting, self.public_setting)

    def test_init_default_parameters(self):
        """Test OnlineEncryptionHandler initialization with default parameters"""
        handler = OnlineEncryptionHandler(self.mock_logger)
        
        self.assertEqual(handler.logger, self.mock_logger)
        self.assertIsNone(handler.security_type)
        self.assertIsNone(handler.public_setting)

    @patch('OnlineEncryptionHandler.uuid.uuid4')
    @patch('OnlineEncryptionHandler.os.path.join')
    def test_handle_success(self, mock_path_join, mock_uuid):
        """Test handle method with successful encryption setup"""
        # Setup mocks
        mock_uuid.return_value = Mock()
        mock_uuid.return_value.__str__ = Mock(return_value="test-uuid")
        mock_path_join.return_value = "/dev/sdb1"
        
        # Create test device item
        device_item = DeviceItem()
        device_item.name = "sdb1"
        device_item.file_system = "ext4"
        device_item.mount_point = "/mnt/data"
        device_item.size = 10737418240  # 10GB
        
        # Setup mocks for dependencies
        mock_disk_util = Mock()
        mock_disk_util.get_luks_header_size.return_value = 16777216  # 16MB
        mock_disk_util.check_shrink_fs.return_value = CommonVariables.process_success
        mock_disk_util.umount.return_value = CommonVariables.success
        
        mock_crypt_mount_config_util = Mock()
        mock_bek_util = Mock()
        passphrase_file = "/path/to/passphrase"
        
        with patch.object(self.handler.command_executor, 'ExecuteInBash', return_value=CommonVariables.success):
            with patch.object(self.handler, 'update_crypttab_and_fstab') as mock_update:
                mock_crypt_item = CryptItem()
                mock_update.return_value = mock_crypt_item
                
                # Call the method
                result = self.handler.handle(
                    [device_item], 
                    passphrase_file, 
                    mock_disk_util, 
                    mock_crypt_mount_config_util, 
                    mock_bek_util
                )
                
                # Verify calls
                mock_disk_util.umount.assert_called_once_with("/mnt/data")
                mock_disk_util.check_shrink_fs.assert_called_once()
                mock_update.assert_called_once()
                
                # Verify device was added to queue
                self.assertFalse(self.handler.devices.empty())

    def test_handle_unsupported_filesystem(self):
        """Test handle method with unsupported filesystem"""
        # Create test device item with unsupported filesystem
        device_item = DeviceItem()
        device_item.name = "sdb1"
        device_item.file_system = "ntfs"  # Unsupported
        device_item.mount_point = "/mnt/data"
        device_item.size = 10737418240
        
        mock_disk_util = Mock()
        mock_crypt_mount_config_util = Mock()
        mock_bek_util = Mock()
        passphrase_file = "/path/to/passphrase"
        
        # Call the method
        result = self.handler.handle(
            [device_item], 
            passphrase_file, 
            mock_disk_util, 
            mock_crypt_mount_config_util, 
            mock_bek_util
        )
        
        # Verify error was logged and device returned
        self.mock_logger.log.assert_called()
        error_call = [call for call in self.mock_logger.log.call_args_list if 'ErrorLevel' in str(call)]
        self.assertTrue(len(error_call) > 0)
        self.assertEqual(result, device_item)

    def test_handle_umount_failure(self):
        """Test handle method when umount fails"""
        # Create test device item
        device_item = DeviceItem()
        device_item.name = "sdb1"
        device_item.file_system = "ext4"
        device_item.mount_point = "/mnt/data"
        device_item.size = 10737418240
        
        # Setup mocks
        mock_disk_util = Mock()
        mock_disk_util.umount.return_value = 1  # Failure
        
        mock_crypt_mount_config_util = Mock()
        mock_bek_util = Mock()
        passphrase_file = "/path/to/passphrase"
        
        # Call the method
        result = self.handler.handle(
            [device_item], 
            passphrase_file, 
            mock_disk_util, 
            mock_crypt_mount_config_util, 
            mock_bek_util
        )
        
        # Verify error was logged and device returned
        self.mock_logger.log.assert_called()
        self.assertEqual(result, device_item)

    def test_handle_shrink_check_failure(self):
        """Test handle method when shrink check fails"""
        # Create test device item
        device_item = DeviceItem()
        device_item.name = "sdb1"
        device_item.file_system = "ext4"
        device_item.mount_point = "/mnt/data"
        device_item.size = 10737418240
        
        # Setup mocks
        mock_disk_util = Mock()
        mock_disk_util.umount.return_value = CommonVariables.success
        mock_disk_util.get_luks_header_size.return_value = 16777216
        mock_disk_util.check_shrink_fs.return_value = 1  # Failure
        
        mock_crypt_mount_config_util = Mock()
        mock_bek_util = Mock()
        passphrase_file = "/path/to/passphrase"
        
        # Call the method
        result = self.handler.handle(
            [device_item], 
            passphrase_file, 
            mock_disk_util, 
            mock_crypt_mount_config_util, 
            mock_bek_util
        )
        
        # Verify error was logged and device returned
        self.mock_logger.log.assert_called()
        error_calls = [call for call in self.mock_logger.log.call_args_list 
                      if 'ErrorLevel' in str(call)]
        self.assertTrue(len(error_calls) > 0)
        self.assertEqual(result, device_item)

    def test_handle_cryptsetup_failure(self):
        """Test handle method when cryptsetup init fails"""
        # Create test device item
        device_item = DeviceItem()
        device_item.name = "sdb1"
        device_item.file_system = "ext4"
        device_item.mount_point = "/mnt/data"
        device_item.size = 10737418240
        
        # Setup mocks
        mock_disk_util = Mock()
        mock_disk_util.umount.return_value = CommonVariables.success
        mock_disk_util.get_luks_header_size.return_value = 16777216
        mock_disk_util.check_shrink_fs.return_value = CommonVariables.process_success
        
        mock_crypt_mount_config_util = Mock()
        mock_bek_util = Mock()
        passphrase_file = "/path/to/passphrase"
        
        with patch.object(self.handler.command_executor, 'ExecuteInBash', return_value=1):  # Failure
            # Call the method
            result = self.handler.handle(
                [device_item], 
                passphrase_file, 
                mock_disk_util, 
                mock_crypt_mount_config_util, 
                mock_bek_util
            )
            
            # Verify error was logged and device returned
            self.mock_logger.log.assert_called()
            self.assertEqual(result, device_item)

    def test_handle_confidential_vm(self):
        """Test handle method with Confidential VM security type"""
        # Create handler with Confidential VM security type
        handler = OnlineEncryptionHandler(
            self.mock_logger, 
            CommonVariables.ConfidentialVM, 
            self.public_setting
        )
        
        # Create test device item
        device_item = DeviceItem()
        device_item.name = "sdb1"
        device_item.file_system = "ext4"
        device_item.mount_point = "/mnt/data"
        device_item.size = 10737418240
        
        # Setup mocks
        mock_disk_util = Mock()
        mock_disk_util.umount.return_value = CommonVariables.success
        mock_disk_util.get_luks_header_size.return_value = 16777216
        mock_disk_util.check_shrink_fs.return_value = CommonVariables.process_success
        
        mock_crypt_mount_config_util = Mock()
        mock_bek_util = Mock()
        passphrase_file = "/path/to/passphrase"
        
        with patch.object(handler.command_executor, 'ExecuteInBash', return_value=CommonVariables.success):
            with patch.object(handler, 'update_crypttab_and_fstab') as mock_update:
                mock_crypt_item = CryptItem()
                mock_update.return_value = mock_crypt_item
                
                # Call the method
                handler.handle(
                    [device_item], 
                    passphrase_file, 
                    mock_disk_util, 
                    mock_crypt_mount_config_util, 
                    mock_bek_util
                )
                
                # Verify update_crypttab_and_fstab was called with passphrase file
                mock_update.assert_called_once()
                call_args = mock_update.call_args[0]
                self.assertEqual(call_args[-1], passphrase_file)  # Last argument should be passphrase_file

    @patch('OnlineEncryptionHandler.os.path.join')
    def test_update_crypttab_and_fstab(self, mock_path_join):
        """Test update_crypttab_and_fstab method"""
        mock_path_join.return_value = "/dev/mapper/test-uuid"
        
        # Setup mocks
        mock_disk_util = Mock()
        mock_disk_util.get_persistent_path_by_sdx_path.return_value = "/dev/disk/by-uuid/test"
        mock_disk_util.mount_filesystem.return_value = None
        
        mock_crypt_mount_config_util = Mock()
        mock_crypt_mount_config_util.modify_fstab_entry_encrypt.return_value = None
        mock_crypt_mount_config_util.add_crypt_item.return_value = True
        
        # Call the method
        result = self.handler.update_crypttab_and_fstab(
            mock_disk_util,
            mock_crypt_mount_config_util,
            "test-uuid",
            "/dev/sdb1",
            "ext4",
            "/mnt/data"
        )
        
        # Verify the result
        self.assertIsInstance(result, CryptItem)
        self.assertEqual(result.mapper_name, "test-uuid")
        self.assertEqual(result.dev_path, "/dev/disk/by-uuid/test")
        self.assertEqual(result.file_system, "ext4")
        self.assertEqual(result.mount_point, "/mnt/data")
        self.assertFalse(result.uses_cleartext_key)
        self.assertEqual(result.current_luks_slot, 0)

    def test_update_crypttab_and_fstab_no_mount_point(self):
        """Test update_crypttab_and_fstab method with no mount point"""
        # Setup mocks
        mock_disk_util = Mock()
        mock_disk_util.get_persistent_path_by_sdx_path.return_value = "/dev/disk/by-uuid/test"
        
        mock_crypt_mount_config_util = Mock()
        mock_crypt_mount_config_util.add_crypt_item.return_value = True
        
        # Call the method with empty mount point
        result = self.handler.update_crypttab_and_fstab(
            mock_disk_util,
            mock_crypt_mount_config_util,
            "test-uuid",
            "/dev/sdb1",
            "ext4",
            ""
        )
        
        # Verify the result
        self.assertEqual(result.mount_point, "None")
        self.mock_logger.log.assert_called()

    def test_get_device_items_for_resume(self):
        """Test get_device_items_for_resume method"""
        # Setup mocks
        mock_crypt_mount_config_util = Mock()
        mock_disk_util = Mock()
        
        # Create test crypt items
        crypt_item1 = CryptItem()
        crypt_item1.dev_path = "/dev/sdb1"
        crypt_item1.keyfile_path = "/path/to/key1"
        
        crypt_item2 = CryptItem()
        crypt_item2.dev_path = "/dev/sdc1"
        crypt_item2.keyfile_path = "/path/to/key2"
        
        mock_crypt_mount_config_util.get_crypt_items.return_value = [crypt_item1, crypt_item2]
        
        # Mock disk_util to return True for first item, False for second
        mock_disk_util.luks_check_reencryption.side_effect = [True, False]
        
        # Call the method
        result = self.handler.get_device_items_for_resume(
            mock_crypt_mount_config_util, 
            mock_disk_util
        )
        
        # Verify the result
        self.assertEqual(result, 1)  # Only one device needs resume
        self.assertFalse(self.handler.devices.empty())
        
        # Get the item from queue and verify
        item = self.handler.devices.get()
        self.assertEqual(item.crypt_item, crypt_item1)
        self.assertEqual(item.bek_file_path, "/path/to/key1")

    def test_get_online_encryption_item_success(self):
        """Test get_online_encryption_item method with available item"""
        # Add test item to queue
        crypt_item = CryptItem()
        test_item = OnlineEncryptionItem(crypt_item, "/path/to/bek")
        self.handler.devices.put(test_item)
        
        # Create locks
        queue_lock = threading.Lock()
        log_lock = threading.Lock()
        
        # Call the method
        result = self.handler.get_online_encryption_item(queue_lock, log_lock)
        
        # Verify the result
        self.assertEqual(result, test_item)

    def test_get_online_encryption_item_empty_queue(self):
        """Test get_online_encryption_item method with empty queue"""
        # Create locks
        queue_lock = threading.Lock()
        log_lock = threading.Lock()
        
        # Call the method
        result = self.handler.get_online_encryption_item(queue_lock, log_lock)
        
        # Verify the result
        self.assertIsNone(result)

    def test_get_online_encryption_item_exception(self):
        """Test get_online_encryption_item method exception handling"""
        # Create locks
        queue_lock = threading.Lock()
        log_lock = threading.Lock()
        
        # Mock the devices queue to raise exception
        with patch.object(self.handler.devices, 'empty', side_effect=Exception("Queue error")):
            result = self.handler.get_online_encryption_item(queue_lock, log_lock)
            
            # Verify exception handling
            self.assertIsNone(result)

    def test_update_log(self):
        """Test update_log method"""
        log_lock = threading.Lock()
        test_message = "Test log message"
        
        # Call the method
        self.handler.update_log(test_message, log_lock)
        
        # Verify logger was called
        self.mock_logger.log.assert_called_once_with(test_message)

    @patch('OnlineEncryptionHandler.OnlineEncryptionResumer')
    def test_resume_encryption(self, mock_resumer_class):
        """Test resume_encryption method"""
        # Setup test item
        crypt_item = CryptItem()
        crypt_item.dev_path = "/dev/sdb1"
        test_item = OnlineEncryptionItem(crypt_item, "/path/to/bek")
        self.handler.devices.put(test_item)
        
        # Setup mocks
        mock_disk_util = Mock()
        mock_resumer = Mock()
        mock_resumer_class.return_value = mock_resumer
        
        # Create locks
        log_lock = threading.Lock()
        queue_lock = threading.Lock()
        
        # Call the method
        self.handler.resume_encryption(mock_disk_util, log_lock, queue_lock)
        
        # Verify resumer was created and called
        mock_resumer_class.assert_called_once()
        mock_resumer.begin_resume.assert_called_once()

    @patch('OnlineEncryptionHandler.OnlineEncryptionResumer')
    def test_resume_encryption_confidential_vm(self, mock_resumer_class):
        """Test resume_encryption method with Confidential VM"""
        # Create handler with Confidential VM security type
        handler = OnlineEncryptionHandler(
            self.mock_logger, 
            CommonVariables.ConfidentialVM, 
            self.public_setting
        )
        
        # Setup test item
        crypt_item = CryptItem()
        crypt_item.dev_path = "/dev/sdb1"
        test_item = OnlineEncryptionItem(crypt_item, "/path/to/bek")
        handler.devices.put(test_item)
        
        # Setup mocks
        mock_disk_util = Mock()
        mock_resumer = Mock()
        mock_resumer_class.return_value = mock_resumer
        
        # Create locks
        log_lock = threading.Lock()
        queue_lock = threading.Lock()
        
        # Call the method
        handler.resume_encryption(mock_disk_util, log_lock, queue_lock)
        
        # Verify resumer was called with import_token=True
        mock_resumer.begin_resume.assert_called_once()
        call_args = mock_resumer.begin_resume.call_args[0]
        # Third argument should be True for import_token
        self.assertTrue(call_args[2])

    @patch('OnlineEncryptionHandler.threading.Thread')
    def test_handle_resume_encryption(self, mock_thread_class):
        """Test handle_resume_encryption method"""
        # Add test items to queue
        for i in range(3):
            crypt_item = CryptItem()
            test_item = OnlineEncryptionItem(crypt_item, f"/path/to/bek{i}")
            self.handler.devices.put(test_item)
        
        # Setup mocks
        mock_disk_util = Mock()
        mock_threads = [Mock() for _ in range(3)]
        mock_thread_class.side_effect = mock_threads
        
        # Call the method
        self.handler.handle_resume_encryption(mock_disk_util)
        
        # Verify threads were created and started
        self.assertEqual(mock_thread_class.call_count, 3)
        for mock_thread in mock_threads:
            mock_thread.start.assert_called_once()
            mock_thread.join.assert_called_once()


if __name__ == '__main__':
    unittest.main()
