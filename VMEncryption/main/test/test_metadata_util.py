import unittest
import json
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add the test directory to path for console_logger import
sys.path.insert(0, os.path.dirname(__file__))

from MetadataUtil import MetadataUtil
from console_logger import ConsoleLogger

class TestMetadataUtil(unittest.TestCase):
    """Unit tests for MetadataUtil class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.logger = ConsoleLogger()
        self.metadata_util = MetadataUtil(self.logger)
        
        # Sample metadata for testing
        self.vmss_metadata = {
            'compute': {
                'placementGroupId': '12345678-1234-1234-1234-123456789abc',
                'vmScaleSetName': 'test-vmss',
                'name': 'test-vm'
            }
        }
        
        self.non_vmss_metadata = {
            'compute': {
                'placementGroupId': '',
                'name': 'test-vm'
            }
        }

    def test_init(self):
        """Test MetadataUtil initialization."""
        self.assertEqual(self.metadata_util.logger, self.logger)
        self.assertIsNone(self.metadata_util.metadata)

    @patch('MetadataUtil.urlopen')
    @patch('MetadataUtil.Request')
    def test_request_metadata_success(self, mock_request, mock_urlopen):
        """Test successful metadata request."""
        # Mock the response
        mock_response = Mock()
        mock_response.read.return_value.decode.return_value = json.dumps(self.vmss_metadata)
        mock_urlopen.return_value = mock_response
        
        self.metadata_util.request_metadata()
        
        # Verify request was made correctly
        mock_request.assert_called_once_with("http://169.254.169.254/metadata/instance?api-version=2017-08-01")
        mock_request.return_value.add_header.assert_called_once_with('Metadata', 'true')
        mock_urlopen.assert_called_once()
        
        # Verify metadata was set
        self.assertEqual(self.metadata_util.metadata, self.vmss_metadata)

    @patch('MetadataUtil.urlopen')
    @patch('MetadataUtil.Request')
    def test_request_metadata_failure(self, mock_request, mock_urlopen):
        """Test metadata request failure handling."""
        # Mock an exception during request
        mock_urlopen.side_effect = Exception("Network error")
        
        mock_logger = Mock()
        metadata_util = MetadataUtil(mock_logger)
        
        metadata_util.request_metadata()
        
        # Verify error was logged
        mock_logger.log.assert_called_once()
        args, kwargs = mock_logger.log.call_args
        self.assertIn("Metadata request failed:", args[0])
        
        # Verify metadata remains None
        self.assertIsNone(metadata_util.metadata)

    @patch('MetadataUtil.urlopen')
    @patch('MetadataUtil.Request')
    def test_request_metadata_called_only_once(self, mock_request, mock_urlopen):
        """Test that metadata is only requested once (cached)."""
        # Mock the response
        mock_response = Mock()
        mock_response.read.return_value.decode.return_value = json.dumps(self.vmss_metadata)
        mock_urlopen.return_value = mock_response
        
        # Call request_metadata multiple times
        self.metadata_util.request_metadata()
        self.metadata_util.request_metadata()
        self.metadata_util.request_metadata()
        
        # Verify request was made only once
        mock_request.assert_called_once()
        mock_urlopen.assert_called_once()

    def test_is_vmss_with_vmss_metadata(self):
        """Test is_vmss returns True for VMSS instances."""
        # Set metadata directly to avoid HTTP request
        self.metadata_util.metadata = self.vmss_metadata
        
        result = self.metadata_util.is_vmss()
        
        self.assertTrue(result)

    def test_is_vmss_with_non_vmss_metadata(self):
        """Test is_vmss returns False for non-VMSS instances."""
        # Set metadata directly to avoid HTTP request
        self.metadata_util.metadata = self.non_vmss_metadata
        
        result = self.metadata_util.is_vmss()
        
        self.assertFalse(result)

    def test_is_vmss_with_no_metadata(self):
        """Test is_vmss returns False when metadata is None."""
        self.metadata_util.metadata = None
        
        result = self.metadata_util.is_vmss()
        
        self.assertFalse(result)

    def test_is_vmss_with_no_compute_section(self):
        """Test is_vmss returns False when compute section is missing."""
        self.metadata_util.metadata = {'network': {'interface': []}}
        
        result = self.metadata_util.is_vmss()
        
        self.assertFalse(result)

    def test_is_vmss_with_no_placement_group_id(self):
        """Test is_vmss returns False when placementGroupId is missing."""
        self.metadata_util.metadata = {
            'compute': {
                'name': 'test-vm'
            }
        }
        
        result = self.metadata_util.is_vmss()
        
        self.assertFalse(result)

    def test_is_vmss_with_invalid_guid_format(self):
        """Test is_vmss returns False when placementGroupId has invalid GUID format."""
        self.metadata_util.metadata = {
            'compute': {
                'placementGroupId': 'invalid-guid-format',
                'name': 'test-vm'
            }
        }
        
        result = self.metadata_util.is_vmss()
        
        self.assertFalse(result)

    def test_is_vmss_with_uppercase_guid(self):
        """Test is_vmss returns True with uppercase GUID (case insensitive)."""
        self.metadata_util.metadata = {
            'compute': {
                'placementGroupId': '12345678-1234-1234-1234-123456789ABC',
                'name': 'test-vm'
            }
        }
        
        result = self.metadata_util.is_vmss()
        
        self.assertTrue(result)

    def test_is_vmss_with_mixed_case_guid(self):
        """Test is_vmss returns True with mixed case GUID."""
        self.metadata_util.metadata = {
            'compute': {
                'placementGroupId': '12345678-ABCD-efab-1234-123456789AbC',
                'name': 'test-vm'
            }
        }
        
        result = self.metadata_util.is_vmss()
        
        self.assertTrue(result)

    @patch('MetadataUtil.urlopen')
    @patch('MetadataUtil.Request')
    def test_is_vmss_calls_request_metadata(self, mock_request, mock_urlopen):
        """Test that is_vmss calls request_metadata when metadata is None."""
        # Mock the response
        mock_response = Mock()
        mock_response.read.return_value.decode.return_value = json.dumps(self.vmss_metadata)
        mock_urlopen.return_value = mock_response
        
        result = self.metadata_util.is_vmss()
        
        # Verify request was made
        mock_request.assert_called_once()
        self.assertTrue(result)

    @patch('MetadataUtil.urlopen')
    @patch('MetadataUtil.Request')
    def test_request_metadata_json_decode_error(self, mock_request, mock_urlopen):
        """Test metadata request with invalid JSON response."""
        # Mock invalid JSON response
        mock_response = Mock()
        mock_response.read.return_value.decode.return_value = "invalid json"
        mock_urlopen.return_value = mock_response
        
        mock_logger = Mock()
        metadata_util = MetadataUtil(mock_logger)
        
        metadata_util.request_metadata()
        
        # Verify error was logged
        mock_logger.log.assert_called_once()
        args, kwargs = mock_logger.log.call_args
        self.assertIn("Metadata request failed:", args[0])
        
        # Verify metadata remains None
        self.assertIsNone(metadata_util.metadata)

    def test_is_vmss_with_empty_placement_group_id(self):
        """Test is_vmss returns False when placementGroupId is empty string."""
        self.metadata_util.metadata = {
            'compute': {
                'placementGroupId': '',
                'name': 'test-vm'
            }
        }
        
        result = self.metadata_util.is_vmss()
        
        self.assertFalse(result)

    def test_is_vmss_with_whitespace_placement_group_id(self):
        """Test is_vmss returns False when placementGroupId contains only whitespace."""
        self.metadata_util.metadata = {
            'compute': {
                'placementGroupId': '   ',
                'name': 'test-vm'
            }
        }
        
        result = self.metadata_util.is_vmss()
        
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
