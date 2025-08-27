#!/usr/bin/env python

import unittest
import os
import sys
from unittest.mock import patch, mock_open, Mock

# Add the main directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from BuildVersion import GetVersionFromFile


class TestBuildVersion(unittest.TestCase):
    
    def test_get_version_from_file_success(self):
        """Test successfully reading version from file."""
        mock_version_content = "1.2.3\n"
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=mock_version_content)) as mock_file:
            
            result = GetVersionFromFile()
            self.assertEqual(result, mock_version_content)
            
            # Verify the file was opened correctly
            mock_file.assert_called_once()
    
    def test_get_version_from_file_not_exists(self):
        """Test error when version file doesn't exist."""
        with patch('os.path.exists', return_value=False):
            with self.assertRaises(IOError) as context:
                GetVersionFromFile()
            
            self.assertIn('version.txt file cannot be found', str(context.exception))
    
    def test_get_version_file_path_construction(self):
        """Test that the correct file path is constructed."""
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data="test\n")) as mock_file, \
             patch('os.path.dirname') as mock_dirname, \
             patch('os.path.realpath') as mock_realpath, \
             patch('os.path.join') as mock_join:
            
            # Setup mock return values
            mock_realpath.return_value = '/fake/path/BuildVersion.py'
            mock_dirname.return_value = '/fake/path'
            mock_join.return_value = '/fake/path/version.txt'
            
            GetVersionFromFile()
            
            # Verify path construction calls
            mock_realpath.assert_called_once()
            mock_dirname.assert_called_once_with('/fake/path/BuildVersion.py')
            mock_join.assert_called_once_with('/fake/path', 'version.txt')
    
    def test_get_version_with_different_content(self):
        """Test reading various version content formats."""
        test_cases = [
            "1.0.0",
            "2.1.5\n",
            "3.2.1-beta\n",
            "v4.0.0\n",
            ""
        ]
        
        for version_content in test_cases:
            with self.subTest(version=version_content):
                with patch('os.path.exists', return_value=True), \
                     patch('builtins.open', mock_open(read_data=version_content)):
                    
                    result = GetVersionFromFile()
                    self.assertEqual(result, version_content)
    
    def test_get_version_file_read_error(self):
        """Test handling of file read errors."""
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', side_effect=IOError("Permission denied")):
            
            with self.assertRaises(IOError) as context:
                GetVersionFromFile()
            
            self.assertIn('Permission denied', str(context.exception))


if __name__ == '__main__':
    unittest.main()
