#!/usr/bin/env python

import unittest
import tempfile
import os
import shutil
from unittest.mock import Mock, patch, MagicMock
import sys

# Add the parent directory to sys.path to import the module under test
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from EncryptionMarkConfig import EncryptionMarkConfig
from Common import CommonVariables


class TestEncryptionMarkConfig(unittest.TestCase):
    def setUp(self):
        self.mock_logger = Mock()
        self.mock_encryption_environment = Mock()
        self.temp_dir = tempfile.mkdtemp()
        self.test_config_path = os.path.join(self.temp_dir, 'test_encryption_config')
        self.mock_encryption_environment.azure_crypt_request_queue_path = self.test_config_path

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch('EncryptionMarkConfig.ConfigUtil')
    def test_init(self, mock_config_util):
        """Test EncryptionMarkConfig initialization"""
        config = EncryptionMarkConfig(self.mock_logger, self.mock_encryption_environment)
        
        self.assertEqual(config.logger, self.mock_logger)
        self.assertEqual(config.encryption_environment, self.mock_encryption_environment)
        self.assertIsNone(config.command)
        self.assertIsNone(config.volume_type)
        self.assertIsNone(config.diskFormatQuery)
        self.assertIsNone(config.encryption_mode)
        self.assertIsNone(config.encryption_phase)
        
        mock_config_util.assert_called_once_with(
            self.mock_encryption_environment.azure_crypt_request_queue_path,
            'encryption_request_queue',
            self.mock_logger
        )

    @patch('EncryptionMarkConfig.ConfigUtil')
    def test_get_volume_type(self, mock_config_util):
        """Test getting volume type"""
        mock_config = Mock()
        mock_config_util.return_value = mock_config
        mock_config.get_config.return_value = "All"
        
        config = EncryptionMarkConfig(self.mock_logger, self.mock_encryption_environment)
        result = config.get_volume_type()
        
        self.assertEqual(result, "All")
        mock_config.get_config.assert_called_once_with(CommonVariables.EncryptionVolumeTypeKey)

    @patch('EncryptionMarkConfig.ConfigUtil')
    def test_get_current_command(self, mock_config_util):
        """Test getting current command"""
        mock_config = Mock()
        mock_config_util.return_value = mock_config
        mock_config.get_config.return_value = "Enable"
        
        config = EncryptionMarkConfig(self.mock_logger, self.mock_encryption_environment)
        result = config.get_current_command()
        
        self.assertEqual(result, "Enable")
        mock_config.get_config.assert_called_once_with(CommonVariables.EncryptionEncryptionOperationKey)

    @patch('EncryptionMarkConfig.ConfigUtil')
    def test_get_encryption_disk_format_query(self, mock_config_util):
        """Test getting disk format query"""
        mock_config = Mock()
        mock_config_util.return_value = mock_config
        mock_config.get_config.return_value = "true"
        
        config = EncryptionMarkConfig(self.mock_logger, self.mock_encryption_environment)
        result = config.get_encryption_disk_format_query()
        
        self.assertEqual(result, "true")
        mock_config.get_config.assert_called_once_with(CommonVariables.EncryptionDiskFormatQueryKey)

    @patch('EncryptionMarkConfig.ConfigUtil')
    def test_get_encryption_mode(self, mock_config_util):
        """Test getting encryption mode"""
        mock_config = Mock()
        mock_config_util.return_value = mock_config
        mock_config.get_config.return_value = "EncryptionAtHost"
        
        config = EncryptionMarkConfig(self.mock_logger, self.mock_encryption_environment)
        result = config.get_encryption_mode()
        
        self.assertEqual(result, "EncryptionAtHost")
        mock_config.get_config.assert_called_once_with(CommonVariables.EncryptionModeKey)

    @patch('EncryptionMarkConfig.ConfigUtil')
    def test_get_encryption_phase(self, mock_config_util):
        """Test getting encryption phase"""
        mock_config = Mock()
        mock_config_util.return_value = mock_config
        mock_config.get_config.return_value = "Initial"
        
        config = EncryptionMarkConfig(self.mock_logger, self.mock_encryption_environment)
        result = config.get_encryption_phase()
        
        self.assertEqual(result, "Initial")
        mock_config.get_config.assert_called_once_with(CommonVariables.EncryptionPhaseKey)

    @patch('EncryptionMarkConfig.ConfigUtil')
    def test_config_file_exists(self, mock_config_util):
        """Test checking if config file exists"""
        mock_config = Mock()
        mock_config_util.return_value = mock_config
        mock_config.config_file_exists.return_value = True
        
        config = EncryptionMarkConfig(self.mock_logger, self.mock_encryption_environment)
        result = config.config_file_exists()
        
        self.assertTrue(result)
        mock_config.config_file_exists.assert_called_once()

    @patch('EncryptionMarkConfig.ConfigUtil')
    @patch('EncryptionMarkConfig.ConfigKeyValuePair')
    def test_commit(self, mock_key_value_pair, mock_config_util):
        """Test committing configuration"""
        mock_config = Mock()
        mock_config_util.return_value = mock_config
        
        # Create mock key-value pairs
        mock_pair = Mock()
        mock_key_value_pair.return_value = mock_pair
        
        config = EncryptionMarkConfig(self.mock_logger, self.mock_encryption_environment)
        config.command = "Enable"
        config.volume_type = "All"
        config.diskFormatQuery = "false"
        config.encryption_mode = "EncryptionAtHost"
        config.encryption_phase = "Initial"
        
        config.commit()
        
        # Verify that 5 key-value pairs were created
        self.assertEqual(mock_key_value_pair.call_count, 5)
        
        # Check the key-value pair creation calls
        expected_calls = [
            unittest.mock.call(CommonVariables.EncryptionEncryptionOperationKey, "Enable"),
            unittest.mock.call(CommonVariables.EncryptionVolumeTypeKey, "All"),
            unittest.mock.call(CommonVariables.EncryptionDiskFormatQueryKey, "false"),
            unittest.mock.call(CommonVariables.EncryptionModeKey, "EncryptionAtHost"),
            unittest.mock.call(CommonVariables.EncryptionPhaseKey, "Initial")
        ]
        mock_key_value_pair.assert_has_calls(expected_calls)
        
        # Verify save_configs was called once
        mock_config.save_configs.assert_called_once()
        saved_pairs = mock_config.save_configs.call_args[0][0]
        self.assertEqual(len(saved_pairs), 5)

    @patch('EncryptionMarkConfig.ConfigUtil')
    def test_clear_config_success(self, mock_config_util):
        """Test clearing config when file exists"""
        config = EncryptionMarkConfig(self.mock_logger, self.mock_encryption_environment)
        
        # Create a test file
        with open(self.test_config_path, 'w') as f:
            f.write("test content")
        
        result = config.clear_config()
        
        self.assertTrue(result)
        self.assertFalse(os.path.exists(self.test_config_path))

    @patch('EncryptionMarkConfig.ConfigUtil')
    def test_clear_config_file_not_exists(self, mock_config_util):
        """Test clearing config when file doesn't exist"""
        config = EncryptionMarkConfig(self.mock_logger, self.mock_encryption_environment)
        
        result = config.clear_config()
        
        self.assertTrue(result)

    @patch('EncryptionMarkConfig.ConfigUtil')
    @patch('os.remove')
    @patch('os.path.exists')
    def test_clear_config_exception(self, mock_exists, mock_remove, mock_config_util):
        """Test clearing config when exception occurs"""
        mock_exists.return_value = True
        mock_remove.side_effect = OSError("Permission denied")
        
        config = EncryptionMarkConfig(self.mock_logger, self.mock_encryption_environment)
        
        result = config.clear_config()
        
        self.assertFalse(result)  # Should return False on exception
        self.mock_logger.log.assert_called_once()
        log_call_args = self.mock_logger.log.call_args[0][0]
        self.assertIn("Failed to clear_queue", log_call_args)

    @patch('EncryptionMarkConfig.ConfigUtil')
    def test_properties_setting_getting(self, mock_config_util):
        """Test setting and getting all properties"""
        config = EncryptionMarkConfig(self.mock_logger, self.mock_encryption_environment)
        
        # Test setting properties
        config.command = "Disable"
        config.volume_type = "OS"
        config.diskFormatQuery = "true"
        config.encryption_mode = "DualPass"
        config.encryption_phase = "Complete"
        
        # Test getting properties
        self.assertEqual(config.command, "Disable")
        self.assertEqual(config.volume_type, "OS")
        self.assertEqual(config.diskFormatQuery, "true")
        self.assertEqual(config.encryption_mode, "DualPass")
        self.assertEqual(config.encryption_phase, "Complete")


if __name__ == '__main__':
    unittest.main()
