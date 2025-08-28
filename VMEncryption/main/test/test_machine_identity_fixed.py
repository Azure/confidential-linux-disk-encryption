import unittest
from unittest.mock import Mock, patch, mock_open, MagicMock
import sys
import os
import xml.dom.minidom

# Add the parent directory to the path to import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from main.MachineIdentity import MachineIdentity


class TestMachineIdentity(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        # Import and create the MachineIdentity instance
        self.machine_identity = MachineIdentity()
    
    def test_init(self):
        """Test MachineIdentity initialization."""
        self.assertIsNotNone(self.machine_identity)
        self.assertIsNotNone(self.machine_identity.store_identity_file)
    
    def test_identity_file_path_construction(self):
        """Test that the identity file path is properly constructed."""
        # The path should be constructed based on CommonVariables
        self.assertIn("machine_identity", self.machine_identity.store_identity_file)
    
    def test_current_identity_success(self):
        """Test successfully reading current identity from XML."""
        xml_content = '''<?xml version="1.0" encoding="utf-8"?>
<HostingEnvironmentConfig>
    <Role guid="12345678-1234-1234-1234-123456789abc">
    </Role>
</HostingEnvironmentConfig>'''
        
        # Patch the specific file path that current_identity uses
        with patch('builtins.open', mock_open(read_data=xml_content)):
            result = self.machine_identity.current_identity()
            
            self.assertEqual(result, "12345678-1234-1234-1234-123456789abc")
    
    def test_current_identity_with_multiple_roles(self):
        """Test reading identity when multiple roles exist (should take first)."""
        xml_content = '''<?xml version="1.0" encoding="utf-8"?>
<HostingEnvironmentConfig>
    <Role guid="first-guid-12345">
    </Role>
    <Role guid="second-guid-67890">
    </Role>
</HostingEnvironmentConfig>'''
        
        with patch('builtins.open', mock_open(read_data=xml_content)):
            result = self.machine_identity.current_identity()
            
            # Should return the first role's guid
            self.assertEqual(result, "first-guid-12345")
    
    def test_current_identity_file_not_found(self):
        """Test behavior when XML file is not found."""
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            with self.assertRaises(FileNotFoundError):
                self.machine_identity.current_identity()
    
    def test_current_identity_invalid_xml(self):
        """Test behavior with invalid XML content."""
        with patch('builtins.open', mock_open(read_data="invalid xml content")):
            with patch('xml.dom.minidom.parseString', side_effect=Exception("Invalid XML")):
                with self.assertRaises(Exception):
                    self.machine_identity.current_identity()
    
    def test_save_identity_success(self):
        """Test successfully saving identity to file."""
        test_guid = "save-test-guid"
        
        # Mock current_identity to return a test GUID
        with patch.object(self.machine_identity, 'current_identity', return_value=test_guid):
            with patch('builtins.open', mock_open()) as mock_file:
                self.machine_identity.save_identity()
                
                # Verify file was opened in binary write mode
                mock_file.assert_called_once_with(self.machine_identity.store_identity_file, 'wb')
                # Verify the GUID was written as UTF-8 bytes
                mock_file().write.assert_called_once_with(test_guid.encode('utf-8'))
    
    def test_save_identity_with_current_identity_error(self):
        """Test save_identity when current_identity raises an error."""
        with patch.object(self.machine_identity, 'current_identity', side_effect=Exception("XML error")):
            with self.assertRaises(Exception):
                self.machine_identity.save_identity()
    
    def test_stored_identity_file_exists(self):
        """Test reading stored identity when file exists."""
        test_identity = "stored-test-identity"
        
        with patch('builtins.open', mock_open(read_data=test_identity)):
            with patch('os.path.exists', return_value=True):
                result = self.machine_identity.stored_identity()
                
                self.assertEqual(result, test_identity)
    
    def test_stored_identity_file_not_exists(self):
        """Test behavior when stored identity file doesn't exist."""
        with patch('os.path.exists', return_value=False):
            result = self.machine_identity.stored_identity()
            
            self.assertIsNone(result)
    
    def test_stored_identity_file_read_error(self):
        """Test behavior when stored identity file exists but can't be read."""
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', side_effect=IOError("Read error")):
                with self.assertRaises(IOError):
                    self.machine_identity.stored_identity()
    
    def test_complete_workflow(self):
        """Test complete workflow of saving and retrieving identity."""
        test_guid = "workflow-test-guid"
        xml_content = f'''<?xml version="1.0" encoding="utf-8"?>
<HostingEnvironmentConfig>
    <Role guid="{test_guid}">
    </Role>
</HostingEnvironmentConfig>'''
        
        def side_effect(filename, *args, **kwargs):
            # Return XML content for the XML file
            if "/var/lib/waagent/HostingEnvironmentConfig.xml" in filename:
                return mock_open(read_data=xml_content).return_value
            # Return save mock for the identity file
            else:
                return mock_open().return_value
        
        with patch('builtins.open', side_effect=side_effect):
            # First call - read XML
            current_id = self.machine_identity.current_identity()
            self.assertEqual(current_id, test_guid)
            
            # Second call - save identity (this also calls current_identity internally)
            self.machine_identity.save_identity()
            
            # Third call - read stored identity
            with patch('builtins.open', mock_open(read_data=test_guid)), \
                 patch('os.path.exists', return_value=True):
                stored_id = self.machine_identity.stored_identity()
                self.assertEqual(stored_id, test_guid)


if __name__ == '__main__':
    unittest.main()
