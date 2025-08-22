#!/usr/bin/env python

import unittest
import os
import traceback
from unittest.mock import Mock, patch, MagicMock

# Add the main directory to the path to import the module
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from DecryptionMarkConfig import DecryptionMarkConfig
from ConfigUtil import ConfigKeyValuePair


class TestDecryptionMarkConfig(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_logger = Mock()
        self.mock_encryption_environment = Mock()
        self.mock_encryption_environment.azure_decrypt_request_queue_path = '/test/decrypt_queue.ini'
        
    def test_init(self):
        """Test initialization of DecryptionMarkConfig."""
        with patch('DecryptionMarkConfig.ConfigUtil') as mock_config_util:
            dmc = DecryptionMarkConfig(self.mock_logger, self.mock_encryption_environment)
            
            self.assertEqual(dmc.logger, self.mock_logger)
            self.assertEqual(dmc.encryption_environment, self.mock_encryption_environment)
            self.assertIsNone(dmc.command)
            self.assertIsNone(dmc.volume_type)
            
            # Verify ConfigUtil was initialized correctly
            mock_config_util.assert_called_once_with(
                '/test/decrypt_queue.ini',
                'decryption_request_queue',
                self.mock_logger
            )
            
    def test_get_current_command(self):
        """Test getting current command."""
        with patch('DecryptionMarkConfig.ConfigUtil') as mock_config_util:
            mock_config_instance = Mock()
            mock_config_util.return_value = mock_config_instance
            mock_config_instance.get_config.return_value = 'Disable'
            
            dmc = DecryptionMarkConfig(self.mock_logger, self.mock_encryption_environment)
            result = dmc.get_current_command()
            
            self.assertEqual(result, 'Disable')
            mock_config_instance.get_config.assert_called_once()
            
    def test_config_file_exists_true(self):
        """Test config_file_exists when file exists."""
        with patch('DecryptionMarkConfig.ConfigUtil') as mock_config_util:
            mock_config_instance = Mock()
            mock_config_util.return_value = mock_config_instance
            mock_config_instance.config_file_exists.return_value = True
            
            dmc = DecryptionMarkConfig(self.mock_logger, self.mock_encryption_environment)
            result = dmc.config_file_exists()
            
            self.assertTrue(result)
            mock_config_instance.config_file_exists.assert_called_once()
            
    def test_config_file_exists_false(self):
        """Test config_file_exists when file doesn't exist."""
        with patch('DecryptionMarkConfig.ConfigUtil') as mock_config_util:
            mock_config_instance = Mock()
            mock_config_util.return_value = mock_config_instance
            mock_config_instance.config_file_exists.return_value = False
            
            dmc = DecryptionMarkConfig(self.mock_logger, self.mock_encryption_environment)
            result = dmc.config_file_exists()
            
            self.assertFalse(result)
            mock_config_instance.config_file_exists.assert_called_once()
            
    def test_commit(self):
        """Test committing configuration."""
        with patch('DecryptionMarkConfig.ConfigUtil') as mock_config_util:
            with patch('DecryptionMarkConfig.CommonVariables') as mock_common_vars:
                mock_common_vars.EncryptionEncryptionOperationKey = 'EncryptionOperation'
                mock_common_vars.EncryptionVolumeTypeKey = 'VolumeType'
                
                mock_config_instance = Mock()
                mock_config_util.return_value = mock_config_instance
                
                dmc = DecryptionMarkConfig(self.mock_logger, self.mock_encryption_environment)
                dmc.command = 'Disable'
                dmc.volume_type = 'OS'
                
                dmc.commit()
                
                # Verify save_configs was called with correct parameters
                mock_config_instance.save_configs.assert_called_once()
                call_args = mock_config_instance.save_configs.call_args[0][0]
                
                # Check that we have 2 key-value pairs
                self.assertEqual(len(call_args), 2)
                
                # Check command key-value pair
                command_pair = call_args[0]
                self.assertEqual(command_pair.prop_name, 'EncryptionOperation')
                self.assertEqual(command_pair.prop_value, 'Disable')
                
                # Check volume_type key-value pair
                volume_type_pair = call_args[1]
                self.assertEqual(volume_type_pair.prop_name, 'VolumeType')
                self.assertEqual(volume_type_pair.prop_value, 'OS')
                
    def test_commit_with_none_values(self):
        """Test committing configuration with None values."""
        with patch('DecryptionMarkConfig.ConfigUtil') as mock_config_util:
            with patch('DecryptionMarkConfig.CommonVariables') as mock_common_vars:
                mock_common_vars.EncryptionEncryptionOperationKey = 'EncryptionOperation'
                mock_common_vars.EncryptionVolumeTypeKey = 'VolumeType'
                
                mock_config_instance = Mock()
                mock_config_util.return_value = mock_config_instance
                
                dmc = DecryptionMarkConfig(self.mock_logger, self.mock_encryption_environment)
                # command and volume_type remain None
                
                dmc.commit()
                
                # Verify save_configs was called
                mock_config_instance.save_configs.assert_called_once()
                call_args = mock_config_instance.save_configs.call_args[0][0]
                
                # Check that we have 2 key-value pairs with None values
                self.assertEqual(len(call_args), 2)
                
                command_pair = call_args[0]
                self.assertEqual(command_pair.prop_name, 'EncryptionOperation')
                self.assertIsNone(command_pair.prop_value)
                
                volume_type_pair = call_args[1]
                self.assertEqual(volume_type_pair.prop_name, 'VolumeType')
                self.assertIsNone(volume_type_pair.prop_value)
                
    def test_clear_config_success(self):
        """Test successfully clearing configuration."""
        with patch('DecryptionMarkConfig.ConfigUtil'):
            with patch('os.path.exists', return_value=True):
                with patch('os.remove') as mock_remove:
                    dmc = DecryptionMarkConfig(self.mock_logger, self.mock_encryption_environment)
                    result = dmc.clear_config()
                    
                    self.assertTrue(result)
                    mock_remove.assert_called_once_with('/test/decrypt_queue.ini')
                    
    def test_clear_config_file_not_exists(self):
        """Test clearing configuration when file doesn't exist."""
        with patch('DecryptionMarkConfig.ConfigUtil'):
            with patch('os.path.exists', return_value=False):
                with patch('os.remove') as mock_remove:
                    dmc = DecryptionMarkConfig(self.mock_logger, self.mock_encryption_environment)
                    result = dmc.clear_config()
                    
                    self.assertTrue(result)
                    mock_remove.assert_not_called()
                    
    def test_clear_config_os_error(self):
        """Test clearing configuration with OS error."""
        with patch('DecryptionMarkConfig.ConfigUtil'):
            with patch('os.path.exists', return_value=True):
                with patch('os.remove', side_effect=OSError("Permission denied")):
                    dmc = DecryptionMarkConfig(self.mock_logger, self.mock_encryption_environment)
                    result = dmc.clear_config()
                    
                    self.assertFalse(result)
                    # Verify error was logged
                    self.mock_logger.log.assert_called_once()
                    log_call_args = self.mock_logger.log.call_args[0][0]
                    self.assertIn("Failed to clear_queue with error", log_call_args)
                    self.assertIn("Permission denied", log_call_args)
                    
    def test_properties_setting_and_getting(self):
        """Test setting and getting command and volume_type properties."""
        with patch('DecryptionMarkConfig.ConfigUtil'):
            dmc = DecryptionMarkConfig(self.mock_logger, self.mock_encryption_environment)
            
            # Test initial state
            self.assertIsNone(dmc.command)
            self.assertIsNone(dmc.volume_type)
            
            # Test setting values
            dmc.command = 'Enable'
            dmc.volume_type = 'Data'
            
            self.assertEqual(dmc.command, 'Enable')
            self.assertEqual(dmc.volume_type, 'Data')
            
            # Test setting different values
            dmc.command = 'Disable'
            dmc.volume_type = 'All'
            
            self.assertEqual(dmc.command, 'Disable')
            self.assertEqual(dmc.volume_type, 'All')
            
    def test_complete_workflow(self):
        """Test complete workflow of DecryptionMarkConfig operations."""
        with patch('DecryptionMarkConfig.ConfigUtil') as mock_config_util:
            with patch('DecryptionMarkConfig.CommonVariables') as mock_common_vars:
                with patch('os.path.exists', return_value=True):
                    with patch('os.remove') as mock_remove:
                        mock_common_vars.EncryptionEncryptionOperationKey = 'EncryptionOperation'
                        mock_common_vars.EncryptionVolumeTypeKey = 'VolumeType'
                        
                        mock_config_instance = Mock()
                        mock_config_util.return_value = mock_config_instance
                        mock_config_instance.config_file_exists.return_value = True
                        mock_config_instance.get_config.return_value = 'Disable'
                        
                        dmc = DecryptionMarkConfig(self.mock_logger, self.mock_encryption_environment)
                        
                        # Test configuration exists
                        self.assertTrue(dmc.config_file_exists())
                        
                        # Test getting current command
                        self.assertEqual(dmc.get_current_command(), 'Disable')
                        
                        # Test setting new values
                        dmc.command = 'Enable'
                        dmc.volume_type = 'OS'
                        
                        # Test committing
                        dmc.commit()
                        mock_config_instance.save_configs.assert_called_once()
                        
                        # Test clearing
                        result = dmc.clear_config()
                        self.assertTrue(result)
                        mock_remove.assert_called_once_with('/test/decrypt_queue.ini')


if __name__ == '__main__':
    unittest.main()
