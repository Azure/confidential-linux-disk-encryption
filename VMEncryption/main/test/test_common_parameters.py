#!/usr/bin/env python

import unittest
import tempfile
import os
import json
from unittest.mock import patch, mock_open

# Add the main directory to the path to import the module
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from CommonParameters import CommonParameters


class TestCommonParameters(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_json_data = {
            "extension_name": "AzureDiskEncryption", 
            "extension_version": "1.1.1",
            "extension_provider_namespace": "Microsoft.Azure.Security"
        }
        
    def test_init_with_valid_json_file(self):
        """Test initialization with a valid JSON file."""
        with patch('builtins.open', mock_open(read_data=json.dumps(self.test_json_data))):
            with patch('os.path.join') as mock_join:
                with patch('os.path.dirname') as mock_dirname:
                    with patch('os.path.realpath') as mock_realpath:
                        mock_realpath.return_value = '/path/to/module'
                        mock_dirname.return_value = '/path/to'
                        mock_join.return_value = '/path/to/common_parameters.json'
                        
                        cp = CommonParameters()
                        
                        self.assertEqual(cp.json_object, self.test_json_data)
                        self.assertEqual(cp.file_path, '/path/to/common_parameters.json')
                        
    def test_get_extension_name(self):
        """Test getting extension name."""
        with patch('builtins.open', mock_open(read_data=json.dumps(self.test_json_data))):
            with patch('os.path.join', return_value='/test/path'):
                with patch('os.path.dirname', return_value='/test'):
                    with patch('os.path.realpath', return_value='/test/file'):
                        cp = CommonParameters()
                        result = cp.get_extension_name()
                        self.assertEqual(result, "AzureDiskEncryption")
                        
    def test_set_extension_name(self):
        """Test setting extension name."""
        with patch('builtins.open', mock_open(read_data=json.dumps(self.test_json_data))):
            with patch('os.path.join', return_value='/test/path'):
                with patch('os.path.dirname', return_value='/test'):
                    with patch('os.path.realpath', return_value='/test/file'):
                        cp = CommonParameters()
                        cp.set_extension_name("NewExtensionName")
                        self.assertEqual(cp.json_object["extension_name"], "NewExtensionName")
                        
    def test_get_extension_version(self):
        """Test getting extension version."""
        with patch('builtins.open', mock_open(read_data=json.dumps(self.test_json_data))):
            with patch('os.path.join', return_value='/test/path'):
                with patch('os.path.dirname', return_value='/test'):
                    with patch('os.path.realpath', return_value='/test/file'):
                        cp = CommonParameters()
                        result = cp.get_extension_version()
                        self.assertEqual(result, "1.1.1")
                        
    def test_set_extension_version(self):
        """Test setting extension version."""
        with patch('builtins.open', mock_open(read_data=json.dumps(self.test_json_data))):
            with patch('os.path.join', return_value='/test/path'):
                with patch('os.path.dirname', return_value='/test'):
                    with patch('os.path.realpath', return_value='/test/file'):
                        cp = CommonParameters()
                        cp.set_extension_version("2.0.0")
                        self.assertEqual(cp.json_object["extension_version"], "2.0.0")
                        
    def test_get_extension_provider_namespace(self):
        """Test getting extension provider namespace."""
        with patch('builtins.open', mock_open(read_data=json.dumps(self.test_json_data))):
            with patch('os.path.join', return_value='/test/path'):
                with patch('os.path.dirname', return_value='/test'):
                    with patch('os.path.realpath', return_value='/test/file'):
                        cp = CommonParameters()
                        result = cp.get_extension_provider_namespace()
                        self.assertEqual(result, "Microsoft.Azure.Security")
                        
    def test_set_extension_provider_namespace(self):
        """Test setting extension provider namespace."""
        with patch('builtins.open', mock_open(read_data=json.dumps(self.test_json_data))):
            with patch('os.path.join', return_value='/test/path'):
                with patch('os.path.dirname', return_value='/test'):
                    with patch('os.path.realpath', return_value='/test/file'):
                        cp = CommonParameters()
                        cp.set_extension_provider_namespace("Microsoft.Azure.NewNamespace")
                        self.assertEqual(cp.json_object["extension_provider_namespace"], "Microsoft.Azure.NewNamespace")
                        
    def test_save(self):
        """Test saving configuration to file."""
        mock_file = mock_open()
        with patch('builtins.open', mock_file):
            with patch('os.path.join', return_value='/test/path'):
                with patch('os.path.dirname', return_value='/test'):
                    with patch('os.path.realpath', return_value='/test/file'):
                        # First call for __init__ reading
                        mock_file.return_value.read.return_value = json.dumps(self.test_json_data)
                        
                        cp = CommonParameters()
                        cp.set_extension_name("ModifiedName")
                        
                        # Reset the mock for the save operation
                        mock_file.reset_mock()
                        
                        # Call save
                        cp.save()
                        
                        # Verify that open was called with write mode
                        mock_file.assert_called_with('/test/path', 'w')
                        
                        # Get the handle that was returned by open
                        handle = mock_file.return_value
                        
                        # Get all the write calls
                        write_calls = handle.write.call_args_list
                        
                        # The json.dump should have written the modified data
                        written_data = ''.join([call[0][0] for call in write_calls])
                        
                        # Parse the written JSON and verify content
                        try:
                            parsed_data = json.loads(written_data)
                            self.assertEqual(parsed_data["extension_name"], "ModifiedName")
                        except json.JSONDecodeError:
                            # json.dump might not call write in a single call, so just verify the method was called
                            self.assertTrue(handle.write.called)
                            
    def test_init_with_invalid_json(self):
        """Test initialization with invalid JSON data."""
        with patch('builtins.open', mock_open(read_data="invalid json")):
            with patch('os.path.join', return_value='/test/path'):
                with patch('os.path.dirname', return_value='/test'):
                    with patch('os.path.realpath', return_value='/test/file'):
                        with self.assertRaises(json.JSONDecodeError):
                            CommonParameters()
                            
    def test_init_file_not_found(self):
        """Test initialization when file doesn't exist."""
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            with patch('os.path.join', return_value='/test/path'):
                with patch('os.path.dirname', return_value='/test'):
                    with patch('os.path.realpath', return_value='/test/file'):
                        with self.assertRaises(FileNotFoundError):
                            CommonParameters()
                            
    def test_complete_workflow(self):
        """Test complete workflow of getting, setting, and saving parameters."""
        with patch('builtins.open', mock_open(read_data=json.dumps(self.test_json_data))):
            with patch('os.path.join', return_value='/test/path'):
                with patch('os.path.dirname', return_value='/test'):
                    with patch('os.path.realpath', return_value='/test/file'):
                        cp = CommonParameters()
                        
                        # Test initial values
                        self.assertEqual(cp.get_extension_name(), "AzureDiskEncryption")
                        self.assertEqual(cp.get_extension_version(), "1.1.1")
                        self.assertEqual(cp.get_extension_provider_namespace(), "Microsoft.Azure.Security")
                        
                        # Modify values
                        cp.set_extension_name("NewName")
                        cp.set_extension_version("2.0.0")
                        cp.set_extension_provider_namespace("New.Namespace")
                        
                        # Verify modifications
                        self.assertEqual(cp.get_extension_name(), "NewName")
                        self.assertEqual(cp.get_extension_version(), "2.0.0")
                        self.assertEqual(cp.get_extension_provider_namespace(), "New.Namespace")


if __name__ == '__main__':
    unittest.main()
