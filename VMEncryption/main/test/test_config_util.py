#!/usr/bin/env python

import unittest
import os
import tempfile
import configparser
from unittest.mock import Mock, patch, mock_open, MagicMock

# Add the main directory to the path to import the module
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ConfigUtil import ConfigUtil, ConfigKeyValuePair


class TestConfigKeyValuePair(unittest.TestCase):
    
    def test_init(self):
        """Test initialization of ConfigKeyValuePair."""
        kvp = ConfigKeyValuePair("test_key", "test_value")
        self.assertEqual(kvp.prop_name, "test_key")
        self.assertEqual(kvp.prop_value, "test_value")
        
    def test_init_with_none_value(self):
        """Test initialization with None value."""
        kvp = ConfigKeyValuePair("test_key", None)
        self.assertEqual(kvp.prop_name, "test_key")
        self.assertIsNone(kvp.prop_value)


class TestConfigUtil(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_logger = Mock()
        self.test_config_path = "/test/config.ini"
        self.test_section = "test_section"
        
    def test_init(self):
        """Test initialization of ConfigUtil."""
        config_util = ConfigUtil(self.test_config_path, self.test_section, self.mock_logger)
        
        self.assertEqual(config_util.config_file_path, self.test_config_path)
        self.assertEqual(config_util.logger, self.mock_logger)
        self.assertEqual(config_util.azure_crypt_config_section, self.test_section)
        
    def test_config_file_exists_true(self):
        """Test config_file_exists when file exists."""
        with patch('os.path.exists', return_value=True):
            config_util = ConfigUtil(self.test_config_path, self.test_section, self.mock_logger)
            result = config_util.config_file_exists()
            self.assertTrue(result)
            
    def test_config_file_exists_false(self):
        """Test config_file_exists when file doesn't exist."""
        with patch('os.path.exists', return_value=False):
            config_util = ConfigUtil(self.test_config_path, self.test_section, self.mock_logger)
            result = config_util.config_file_exists()
            self.assertFalse(result)
            
    def test_save_config_new_file(self):
        """Test saving config to a new file."""
        with patch('os.path.exists', return_value=False):
            with patch('configparser.ConfigParser') as mock_config_parser:
                with patch('ConfigUtil.open', mock_open(), create=True) as mock_file:
                    mock_config = Mock()
                    mock_config_parser.return_value = mock_config
                    mock_config.has_section.return_value = False
                    
                    config_util = ConfigUtil(self.test_config_path, self.test_section, self.mock_logger)
                    config_util.save_config("test_key", "test_value")
                    
                    # Verify section was added
                    mock_config.add_section.assert_called_once_with(self.test_section)
                    
                    # Verify value was set
                    mock_config.set.assert_called_once_with(self.test_section, "test_key", "test_value")
                    
                    # Verify file was opened for writing
                    mock_file.assert_called_once_with(self.test_config_path, 'wb')
                    
                    # Verify config was written
                    mock_config.write.assert_called_once()
                    
    def test_save_config_existing_file(self):
        """Test saving config to an existing file."""
        with patch('os.path.exists', return_value=True):
            with patch('configparser.ConfigParser') as mock_config_parser:
                with patch('ConfigUtil.open', mock_open(), create=True) as mock_file:
                    mock_config = Mock()
                    mock_config_parser.return_value = mock_config
                    mock_config.has_section.return_value = True
                    
                    config_util = ConfigUtil(self.test_config_path, self.test_section, self.mock_logger)
                    config_util.save_config("test_key", "test_value")
                    
                    # Verify file was read
                    mock_config.read.assert_called_once_with(self.test_config_path)
                    
                    # Verify section was not added (already exists)
                    mock_config.add_section.assert_not_called()
                    
                    # Verify value was set
                    mock_config.set.assert_called_once_with(self.test_section, "test_key", "test_value")
                    
    def test_save_configs_multiple_pairs(self):
        """Test saving multiple config key-value pairs."""
        with patch('os.path.exists', return_value=False):
            with patch('configparser.ConfigParser') as mock_config_parser:
                with patch('codecs.open', mock_open()) as mock_file:
                    mock_config = Mock()
                    mock_config_parser.return_value = mock_config
                    mock_config.has_section.return_value = False
                    
                    config_util = ConfigUtil(self.test_config_path, self.test_section, self.mock_logger)
                    
                    key_value_pairs = [
                        ConfigKeyValuePair("key1", "value1"),
                        ConfigKeyValuePair("key2", "value2"),
                        ConfigKeyValuePair("key3", None)  # Should be skipped
                    ]
                    
                    config_util.save_configs(key_value_pairs)
                    
                    # Verify section was added
                    mock_config.add_section.assert_called_once_with(self.test_section)
                    
                    # Verify only non-None values were set
                    self.assertEqual(mock_config.set.call_count, 2)
                    mock_config.set.assert_any_call(self.test_section, "key1", "value1")
                    mock_config.set.assert_any_call(self.test_section, "key2", "value2")
                    
                    # Verify file was opened with codecs for UTF-8
                    mock_file.assert_called_once_with(self.test_config_path, 'w', 'utf-8')
                    
    def test_save_configs_with_integer_values(self):
        """Test saving configs with integer values (should be converted to string)."""
        with patch('os.path.exists', return_value=False):
            with patch('configparser.ConfigParser') as mock_config_parser:
                with patch('codecs.open', mock_open()) as mock_file:
                    mock_config = Mock()
                    mock_config_parser.return_value = mock_config
                    mock_config.has_section.return_value = False
                    
                    config_util = ConfigUtil(self.test_config_path, self.test_section, self.mock_logger)
                    
                    key_value_pairs = [
                        ConfigKeyValuePair(123, 456)  # Both key and value are integers
                    ]
                    
                    config_util.save_configs(key_value_pairs)
                    
                    # Verify values were converted to strings
                    mock_config.set.assert_called_once_with(self.test_section, "123", "456")
                    
    def test_get_config_existing_file_existing_value(self):
        """Test getting config value from existing file."""
        with patch('os.path.exists', return_value=True):
            with patch('configparser.ConfigParser') as mock_config_parser:
                mock_config = Mock()
                mock_config_parser.return_value = mock_config
                mock_config.get.return_value = "test_value"
                
                config_util = ConfigUtil(self.test_config_path, self.test_section, self.mock_logger)
                result = config_util.get_config("test_key")
                
                self.assertEqual(result, "test_value")
                
                # Verify file was read
                mock_config.read.assert_called_once_with(self.test_config_path)
                
                # Verify value was retrieved
                mock_config.get.assert_called_once_with(self.test_section, "test_key")
                
    def test_get_config_file_not_exists(self):
        """Test getting config when file doesn't exist."""
        with patch('os.path.exists', return_value=False):
            config_util = ConfigUtil(self.test_config_path, self.test_section, self.mock_logger)
            result = config_util.get_config("test_key")
            
            self.assertIsNone(result)
            
            # Verify error was logged
            self.mock_logger.log.assert_called_once()
            log_message = self.mock_logger.log.call_args[0][0]
            self.assertIn("does not exist", log_message)
            
    def test_get_config_no_section_error(self):
        """Test getting config when section doesn't exist."""
        with patch('os.path.exists', return_value=True):
            with patch('configparser.ConfigParser') as mock_config_parser:
                mock_config = Mock()
                mock_config_parser.return_value = mock_config
                mock_config.get.side_effect = configparser.NoSectionError(self.test_section)
                
                config_util = ConfigUtil(self.test_config_path, self.test_section, self.mock_logger)
                result = config_util.get_config("test_key")
                
                self.assertIsNone(result)
                
                # Verify error was logged
                self.mock_logger.log.assert_called_once()
                log_message = self.mock_logger.log.call_args[1]['msg']
                self.assertIn("not found", log_message)
                
    def test_get_config_no_option_error(self):
        """Test getting config when option doesn't exist."""
        with patch('os.path.exists', return_value=True):
            with patch('configparser.ConfigParser') as mock_config_parser:
                mock_config = Mock()
                mock_config_parser.return_value = mock_config
                mock_config.get.side_effect = configparser.NoOptionError("test_key", self.test_section)
                
                config_util = ConfigUtil(self.test_config_path, self.test_section, self.mock_logger)
                result = config_util.get_config("test_key")
                
                self.assertIsNone(result)
                
                # Verify error was logged
                self.mock_logger.log.assert_called_once()
                log_message = self.mock_logger.log.call_args[1]['msg']
                self.assertIn("not found", log_message)
                
    def test_complete_workflow(self):
        """Test complete workflow of saving and retrieving config."""
        with patch('os.path.exists', side_effect=[False, True, True]):  # First save, then get
            with patch('configparser.ConfigParser') as mock_config_parser:
                with patch('codecs.open', mock_open()) as mock_file:
                    mock_config = Mock()
                    mock_config_parser.return_value = mock_config
                    mock_config.has_section.return_value = False
                    mock_config.get.return_value = "retrieved_value"
                    
                    config_util = ConfigUtil(self.test_config_path, self.test_section, self.mock_logger)
                    
                    # Save multiple configs
                    key_value_pairs = [
                        ConfigKeyValuePair("key1", "value1"),
                        ConfigKeyValuePair("key2", "value2")
                    ]
                    config_util.save_configs(key_value_pairs)
                    
                    # Verify save operations
                    mock_config.add_section.assert_called_with(self.test_section)
                    self.assertEqual(mock_config.set.call_count, 2)
                    
                    # Retrieve a config
                    result = config_util.get_config("key1")
                    self.assertEqual(result, "retrieved_value")
                    
    def test_save_config_property_key_value_pair_access(self):
        """Test that ConfigKeyValuePair properties are accessed correctly in save_configs."""
        with patch('os.path.exists', return_value=False):
            with patch('configparser.ConfigParser') as mock_config_parser:
                with patch('codecs.open', mock_open()) as mock_file:
                    mock_config = Mock()
                    mock_config_parser.return_value = mock_config
                    mock_config.has_section.return_value = False
                    
                    config_util = ConfigUtil(self.test_config_path, self.test_section, self.mock_logger)
                    
                    # Create ConfigKeyValuePair with prop_name and prop_value
                    kvp = ConfigKeyValuePair("test_prop", "test_val")
                    
                    config_util.save_configs([kvp])
                    
                    # Verify that prop_name and prop_value were accessed correctly
                    mock_config.set.assert_called_once_with(self.test_section, "test_prop", "test_val")


if __name__ == '__main__':
    unittest.main()
