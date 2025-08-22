import unittest
import sys
import EncryptionSettingsUtil
import Common
from io import StringIO
from console_logger import ConsoleLogger

try:
    import unittest.mock as mock # python 3+ 
except ImportError:
    import mock # python2

# Mock XML modules to avoid import issues
sys.modules['xml'] = mock.MagicMock()
sys.modules['xml.etree'] = mock.MagicMock()
sys.modules['xml.etree.ElementTree'] = mock.MagicMock()

class TestEncryptionSettingsUtil(unittest.TestCase):
    """ unit tests for functions in the check_util module """
    def setUp(self):
        self.logger = ConsoleLogger()
        self.es_util = EncryptionSettingsUtil.EncryptionSettingsUtil(self.logger)

    @mock.patch('time.sleep') # To speed up this test.
    @mock.patch('EncryptionSettingsUtil.EncryptionSettingsUtil.write_settings_file')
    @mock.patch('EncryptionSettingsUtil.EncryptionSettingsUtil.get_index')
    @mock.patch('os.path.isfile', return_value=True)
    @mock.patch('EncryptionSettingsUtil.EncryptionSettingsUtil.get_http_util')
    def test_post_to_wire_server(self, get_http_util, os_path_isfile, get_index, write_settings_file, time_sleep):
        get_http_util.return_value = mock.MagicMock() # Return a mock object
        get_index.return_value = 0
        data = {"Protectors" : "mock data"}

        get_http_util.return_value.Call.return_value.status = 500 # make it so that the http call returns a 500
        self.assertRaises(Exception, self.es_util.post_to_wireserver, data)
        self.assertEqual(get_http_util.return_value.Call.call_count, 3)
        self.assertEqual(write_settings_file.call_count, 0)

        get_http_util.return_value.Call.reset_mock()

        get_http_util.return_value.Call.return_value.status = 400 # make it so that the http call returns a 400
        self.assertRaises(Exception, self.es_util.post_to_wireserver, data)
        self.assertEqual(get_http_util.return_value.Call.call_count, 3)
        self.assertEqual(write_settings_file.call_count, 0)

        get_http_util.return_value.Call.reset_mock()

        get_http_util.return_value.Call.return_value.status = 200 # make it so that the http call returns a 200
        self.es_util.post_to_wireserver(data)
        self.assertEqual(get_http_util.return_value.Call.call_count, 1)
        self.assertEqual(write_settings_file.call_count, 0)

        get_http_util.return_value.Call.reset_mock()

        get_http_util.return_value.Call.return_value = None # Make it so that the HTTP call returns nothing
        self.assertRaises(Exception, self.es_util.post_to_wireserver, data)
        self.assertEqual(get_http_util.return_value.Call.call_count, 3)
        self.assertEqual(write_settings_file.call_count, 0)

    @mock.patch('EncryptionSettingsUtil.ET.fromstring')
    def test_get_fault_reason_correct_xml(self, fromstring_mock):
        # Mock the XML parsing
        detail_element_mock = mock.MagicMock()
        detail_element_mock.text = "The fault reason was: '  0xc1425072  RUNTIME_E_KEYVAULT_SET_SECRET_FAILED  Failed to set secret to KeyVault '."
        
        xml_root_mock = mock.MagicMock()
        xml_root_mock.find.return_value = detail_element_mock
        fromstring_mock.return_value = xml_root_mock
        
        mock_error_xml = "<?xml version='1.0' encoding='utf-8'?>\
                          <Error xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' xmlns:xsd='http://www.w3.org/2001/XMLSchema'>\
                          <Code>BadRequest</Code>\
                          <Message>The request contents are invalid or incomplete. Please refresh your resource cache and retry.</Message>\
                          <Details>The fault reason was: '  0xc1425072  RUNTIME_E_KEYVAULT_SET_SECRET_FAILED  Failed to set secret to KeyVault '.</Details></Error>"
        reason = self.es_util.get_fault_reason(mock_error_xml)
        self.assertEqual(reason, "The fault reason was: '  0xc1425072  RUNTIME_E_KEYVAULT_SET_SECRET_FAILED  Failed to set secret to KeyVault '.")

    @mock.patch('EncryptionSettingsUtil.ET.fromstring')
    def test_get_fault_reason_invalid_xml(self, fromstring_mock):
        # Mock XML parsing to raise an exception for invalid XML
        fromstring_mock.side_effect = Exception("Invalid XML")
        
        mock_invalid_xml = "This is inavlid xml"
        reason = self.es_util.get_fault_reason(mock_invalid_xml)
        self.assertEqual(reason, "Unknown")

    @mock.patch('EncryptionSettingsUtil.ET.fromstring')
    def test_get_fault_reason_no_detail_element(self, fromstring_mock):
        # Mock the XML parsing with no Details element
        xml_root_mock = mock.MagicMock()
        xml_root_mock.find.return_value = None
        fromstring_mock.return_value = xml_root_mock
        
        mock_error_xml = "<?xml version='1.0' encoding='utf-8'?>\
                          <Error xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' xmlns:xsd='http://www.w3.org/2001/XMLSchema'>\
                          <Code>BadRequest</Code>\
                          <Message>The request contents are invalid or incomplete. Please refresh your resource cache and retry.</Message></Error>"
        reason = self.es_util.get_fault_reason(mock_error_xml)
        self.assertEqual(reason, "Unknown")

    @mock.patch('EncryptionSettingsUtil.ET.fromstring')
    def test_get_fault_reason_no_detail_element_text(self, fromstring_mock):
        # Mock the XML parsing with Details element but no text
        detail_element_mock = mock.MagicMock()
        detail_element_mock.text = None
        
        xml_root_mock = mock.MagicMock()
        xml_root_mock.find.return_value = detail_element_mock
        fromstring_mock.return_value = xml_root_mock
        
        mock_error_xml = "<?xml version='1.0' encoding='utf-8'?>\
                          <Error xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' xmlns:xsd='http://www.w3.org/2001/XMLSchema'>\
                          <Code>BadRequest</Code>\
                          <Message>The request contents are invalid or incomplete. Please refresh your resource cache and retry.</Message>\
                          <Details></Details></Error>"
        reason = self.es_util.get_fault_reason(mock_error_xml)
        self.assertEqual(reason, "Unknown")
