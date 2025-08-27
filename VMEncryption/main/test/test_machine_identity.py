import unittest
import tempfile
import os
from unittest.mock import patch, mock_open, MagicMock

from MachineIdentity import MachineIdentity


class TestMachineIdentity(unittest.TestCase):
    """Unit tests for MachineIdentity module"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.machine_identity = MachineIdentity()
        self.test_guid = "12345678-1234-1234-1234-123456789ABC"

    def test_init(self):
        """Test MachineIdentity initialization."""
        identity = MachineIdentity()
        expected_file = './machine_identity_FD76C85E-406F-4CFA-8EB0-CF18B123365C'
        self.assertEqual(identity.store_identity_file, expected_file)

    @patch('builtins.open', new_callable=mock_open)
    def test_current_identity_file_not_found(self, mock_file):
        """Test current_identity method when file doesn't exist."""
        mock_file.side_effect = FileNotFoundError("File not found")
        
        with self.assertRaises(FileNotFoundError):
            self.machine_identity.current_identity()

    @patch('builtins.open', new_callable=mock_open)
    @patch.object(MachineIdentity, 'current_identity')
    def test_save_identity_success(self, mock_current_identity, mock_file):
        """Test save_identity method successfully saves identity."""
        mock_current_identity.return_value = self.test_guid
        
        self.machine_identity.save_identity()
        
        # Verify current_identity was called
        mock_current_identity.assert_called_once()
        
        # Verify file was opened in write binary mode
        mock_file.assert_called_once_with(self.machine_identity.store_identity_file, 'wb')
        
        # Verify the GUID was written as UTF-8 bytes
        mock_file.return_value.write.assert_called_once_with(self.test_guid.encode('utf-8'))

    @patch('builtins.open', new_callable=mock_open)
    @patch.object(MachineIdentity, 'current_identity')
    def test_save_identity_with_unicode_guid(self, mock_current_identity, mock_file):
        """Test save_identity method with unicode characters in GUID."""
        unicode_guid = "12345678-1234-1234-1234-123456789ABC-ñ"
        mock_current_identity.return_value = unicode_guid
        
        self.machine_identity.save_identity()
        
        mock_file.return_value.write.assert_called_once_with(unicode_guid.encode('utf-8'))

    @patch('builtins.open', new_callable=mock_open)
    @patch.object(MachineIdentity, 'current_identity')
    def test_save_identity_file_write_error(self, mock_current_identity, mock_file):
        """Test save_identity method when file write fails."""
        mock_current_identity.return_value = self.test_guid
        mock_file.side_effect = IOError("Cannot write file")
        
        with self.assertRaises(IOError):
            self.machine_identity.save_identity()

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_stored_identity_file_exists(self, mock_file, mock_exists):
        """Test stored_identity method when file exists."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = self.test_guid
        
        result = self.machine_identity.stored_identity()
        
        mock_exists.assert_called_once_with(self.machine_identity.store_identity_file)
        mock_file.assert_called_once_with(self.machine_identity.store_identity_file, 'r')
        self.assertEqual(result, self.test_guid)

    @patch('os.path.exists')
    def test_stored_identity_file_not_exists(self, mock_exists):
        """Test stored_identity method when file doesn't exist."""
        mock_exists.return_value = False
        
        result = self.machine_identity.stored_identity()
        
        mock_exists.assert_called_once_with(self.machine_identity.store_identity_file)
        self.assertIsNone(result)

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_stored_identity_empty_file(self, mock_file, mock_exists):
        """Test stored_identity method with empty file."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = ""
        
        result = self.machine_identity.stored_identity()
        
        self.assertEqual(result, "")

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_stored_identity_file_read_error(self, mock_file, mock_exists):
        """Test stored_identity method when file read fails."""
        mock_exists.return_value = True
        mock_file.side_effect = IOError("Cannot read file")
        
        with self.assertRaises(IOError):
            self.machine_identity.stored_identity()

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_stored_identity_with_whitespace(self, mock_file, mock_exists):
        """Test stored_identity method with whitespace in stored content."""
        mock_exists.return_value = True
        guid_with_whitespace = f"  {self.test_guid}  \n"
        mock_file.return_value.read.return_value = guid_with_whitespace
        
        result = self.machine_identity.stored_identity()
        
        # Should return content as-is (including whitespace)
        self.assertEqual(result, guid_with_whitespace)

    def test_integration_save_and_retrieve(self):
        """Integration test: save identity and then retrieve it."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Use a temporary file for testing
            temp_file = os.path.join(temp_dir, "test_identity_file")
            self.machine_identity.store_identity_file = temp_file
            
            # Mock current_identity to return test GUID
            with patch.object(self.machine_identity, 'current_identity', return_value=self.test_guid):
                # Save the identity
                self.machine_identity.save_identity()
                
                # Retrieve the stored identity
                stored = self.machine_identity.stored_identity()
                
                # Should match the original GUID
                self.assertEqual(stored, self.test_guid)


if __name__ == '__main__':
    unittest.main()
