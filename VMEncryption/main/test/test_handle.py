#!/usr/bin/env python

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock, mock_open

# Add the parent directory to the path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock the problematic imports before importing handle
sys.modules['Utils'] = Mock()
sys.modules['Utils.HandlerUtil'] = Mock()
sys.modules['waagent'] = Mock()
sys.modules['xml'] = Mock()
sys.modules['xml.parsers'] = Mock()
sys.modules['xml.parsers.expat'] = Mock()

# Mock the waagent loading to avoid Windows compatibility issues
with patch('sys.modules', {**sys.modules, 'waagent': Mock(), 'xml': Mock(), 'xml.parsers': Mock(), 'xml.parsers.expat': Mock()}):
    import handle

from Common import CommonVariables

class TestHandleFunctions(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_hutil = Mock()
        self.mock_logger = Mock()
        self.mock_encryption_environment = Mock()
        self.mock_distro_patcher = Mock()
        
        # Set up mock attributes
        self.mock_distro_patcher.distro_info = ['ubuntu', '18.04']
        self.mock_distro_patcher.support_online_encryption = True

    def test_install(self):
        """Test install function"""
        with patch.object(handle, 'hutil', self.mock_hutil):
            handle.install()
            
            self.mock_hutil.do_parse_context.assert_called_once_with('Install')
            self.mock_hutil.do_exit.assert_called_once_with(
                0, 'Install', CommonVariables.extension_success_status, 
                str(CommonVariables.success), 'Install Succeeded'
            )

    def test_disable(self):
        """Test disable function"""
        with patch.object(handle, 'hutil', self.mock_hutil), \
             patch.object(handle, 'security_Type', CommonVariables.ConfidentialVM), \
             patch.object(handle, 'logger', self.mock_logger), \
             patch('handle.VolumeNotificationService') as mock_vns:
            
            mock_vns_instance = Mock()
            mock_vns.return_value = mock_vns_instance
            
            handle.disable()
            
            self.mock_hutil.do_parse_context.assert_called_once_with('Disable')
            self.mock_hutil.archive_old_configs.assert_called_once()

    def test_uninstall(self):
        """Test uninstall function"""
        with patch.object(handle, 'hutil', self.mock_hutil), \
             patch.object(handle, 'security_Type', CommonVariables.ConfidentialVM), \
             patch.object(handle, 'logger', self.mock_logger), \
             patch('handle.VolumeNotificationService') as mock_vns:
            
            mock_vns_instance = Mock()
            mock_vns.return_value = mock_vns_instance
            
            handle.uninstall()
            
            self.mock_hutil.do_parse_context.assert_called_once_with('Uninstall')

    @patch('handle.DiskUtil')
    @patch('handle.CryptMountConfigUtil')
    @patch('handle.BekUtil')
    @patch('handle.EncryptionSettingsUtil')
    @patch('handle.start_daemon')
    @patch('handle.ExtensionParameter')
    @patch('handle.DecryptionMarkConfig')
    @patch('handle.json.loads')
    @patch.object(handle, 'vns_call', False)
    def test_disable_encryption(self, mock_json_loads, mock_decryption_config, mock_ext_param, 
                               mock_start_daemon, mock_settings_util, mock_bek_util, 
                               mock_crypt_util, mock_disk_util):
        """Test disable_encryption function"""
        # Set up proper hutil mock with context structure
        mock_hutil = Mock()
        mock_hutil._context._config = {
            'runtimeSettings': [{
                'handlerSettings': {
                    'publicSettings': {'VolumeType': 'Data'},
                    'protectedSettings': {'Passphrase': 'test123'}
                }
            }]
        }
        
        # Mock json.loads to return the expected encryption status
        mock_json_loads.return_value = {"os": "NotEncrypted", "data": "NotEncrypted"}
        
        with patch.object(handle, 'hutil', mock_hutil), \
             patch.object(handle, 'logger', self.mock_logger), \
             patch.object(handle, 'DistroPatcher', self.mock_distro_patcher), \
             patch.object(handle, 'encryption_environment', self.mock_encryption_environment):
            
            # Set up mocks for utility classes
            mock_decryption_marker = Mock()
            mock_decryption_config.return_value = mock_decryption_marker
            
            mock_extension_param_instance = Mock()
            mock_ext_param.return_value = mock_extension_param_instance
            
            # Mock DiskUtil instance - this is key to prevent /proc/mounts access
            mock_disk_util_instance = Mock()
            mock_disk_util.return_value = mock_disk_util_instance
            # Mock get_encryption_status directly to return the JSON string
            mock_disk_util_instance.get_encryption_status.return_value = '{"os": "NotEncrypted", "data": "NotEncrypted"}'
            # Mock get_mount_items to prevent /proc/mounts access
            mock_disk_util_instance.get_mount_items.return_value = []
            
            mock_bek_util_instance = Mock()
            mock_bek_util.return_value = mock_bek_util_instance
            mock_bek_util_instance.get_bek_passphrase_file.return_value = "/test/passphrase"
            
            mock_crypt_util_instance = Mock()
            mock_crypt_util.return_value = mock_crypt_util_instance
            mock_crypt_util_instance.get_crypt_items.return_value = []
            
            try:
                handle.disable_encryption()
            except SystemExit:
                pass  # Expected due to exit call
                
            mock_hutil.do_parse_context.assert_called_once_with('DisableEncryption')
            # Check that logger was called - may be called with error message due to mocking
            self.assertTrue(self.mock_logger.log.called)

    def test_none_or_empty_with_none(self):
        """Test none_or_empty function with None"""
        result = handle.none_or_empty(None)
        self.assertTrue(result)

    def test_none_or_empty_with_empty_string(self):
        """Test none_or_empty function with empty string"""
        result = handle.none_or_empty("")
        self.assertTrue(result)

    def test_none_or_empty_with_value(self):
        """Test none_or_empty function with actual value"""
        result = handle.none_or_empty("test")
        self.assertFalse(result)

    @patch('handle.sys.argv', ['script.py', 'arg1', 'arg2'])
    def test_is_vns_call_false(self):
        """Test is_vns_call returns False when not VNS call"""
        result = handle.is_vns_call()
        self.assertFalse(result)

    @patch('handle.sys.argv', ['handle.py', '-vnscall'])
    def test_is_vns_call_true(self):
        """Test is_vns_call returns True when VNS call"""
        result = handle.is_vns_call()
        self.assertTrue(result)

    def test_not_support_header_option_distro_centos6(self):
        """Test not_support_header_option_distro for CentOS 6"""
        mock_patcher = Mock()
        mock_patcher.distro_info = ['centos', '6.5']
        result = handle.not_support_header_option_distro(mock_patcher)
        self.assertTrue(result)

    def test_not_support_header_option_distro_redhat6(self):
        """Test not_support_header_option_distro for RedHat 6"""
        mock_patcher = Mock()
        mock_patcher.distro_info = ['redhat', '6.8']
        result = handle.not_support_header_option_distro(mock_patcher)
        self.assertTrue(result)

    def test_not_support_header_option_distro_suse11(self):
        """Test not_support_header_option_distro for SUSE 11"""
        mock_patcher = Mock()
        mock_patcher.distro_info = ['suse', '11.4']
        result = handle.not_support_header_option_distro(mock_patcher)
        self.assertTrue(result)

    def test_not_support_header_option_distro_ubuntu(self):
        """Test not_support_header_option_distro for supported distro"""
        mock_patcher = Mock()
        mock_patcher.distro_info = ['ubuntu', '18.04']
        result = handle.not_support_header_option_distro(mock_patcher)
        self.assertFalse(result)

    def test_toggle_se_linux_for_centos7_true(self):
        """Test toggle_se_linux_for_centos7 for CentOS 7.0"""
        with patch.object(handle, 'DistroPatcher', self.mock_distro_patcher), \
             patch.object(handle, 'encryption_environment', self.mock_encryption_environment):
            
            self.mock_distro_patcher.distro_info = ['centos', '7.0.1']
            self.mock_encryption_environment.get_se_linux.return_value = 'enforcing'
            result = handle.toggle_se_linux_for_centos7(True)
            self.assertTrue(result)

    def test_toggle_se_linux_for_centos7_false(self):
        """Test toggle_se_linux_for_centos7 for non-CentOS 7.0"""
        with patch.object(handle, 'DistroPatcher', self.mock_distro_patcher):
            self.mock_distro_patcher.distro_info = ['ubuntu', '18.04']
            result = handle.toggle_se_linux_for_centos7(True)
            self.assertFalse(result)

    def test_get_public_settings_string(self):
        """Test get_public_settings when settings is a string"""
        with patch.object(handle, 'hutil', self.mock_hutil):
            settings_str = '{"VolumeType": "All"}'
            self.mock_hutil._context._config = {
                'runtimeSettings': [{'handlerSettings': {'publicSettings': settings_str}}]
            }
            
            with patch('json.loads') as mock_json:
                mock_json.return_value = {"VolumeType": "All"}
                result = handle.get_public_settings()
                mock_json.assert_called_once_with(settings_str)
                self.assertEqual(result, {"VolumeType": "All"})

    def test_get_public_settings_dict(self):
        """Test get_public_settings when settings is already a dict"""
        with patch.object(handle, 'hutil', self.mock_hutil):
            settings_dict = {"VolumeType": "All"}
            self.mock_hutil._context._config = {
                'runtimeSettings': [{'handlerSettings': {'publicSettings': settings_dict}}]
            }
            
            result = handle.get_public_settings()
            self.assertEqual(result, settings_dict)

    def test_get_protected_settings_string(self):
        """Test get_protected_settings when settings is a string"""
        with patch.object(handle, 'hutil', self.mock_hutil):
            settings_str = '{"Passphrase": "secret"}'
            self.mock_hutil._context._config = {
                'runtimeSettings': [{'handlerSettings': {'protectedSettings': settings_str}}]
            }
            
            with patch('json.loads') as mock_json:
                mock_json.return_value = {"Passphrase": "secret"}
                result = handle.get_protected_settings()
                mock_json.assert_called_once_with(settings_str)
                self.assertEqual(result, {"Passphrase": "secret"})

    def test_get_protected_settings_dict(self):
        """Test get_protected_settings when settings is already a dict"""
        with patch.object(handle, 'hutil', self.mock_hutil):
            settings_dict = {"Passphrase": "secret"}
            self.mock_hutil._context._config = {
                'runtimeSettings': [{'handlerSettings': {'protectedSettings': settings_dict}}]
            }
            
            result = handle.get_protected_settings()
            self.assertEqual(result, settings_dict)

    def test_are_disks_stamped_with_current_config_true(self):
        """Test are_disks_stamped_with_current_config returns True"""
        with patch.object(handle, 'hutil', self.mock_hutil):
            mock_config = Mock()
            mock_config.get_secret_seq_num.return_value = "5"
            self.mock_hutil.get_current_seq.return_value = 5
            
            result = handle.are_disks_stamped_with_current_config(mock_config)
            self.assertTrue(result)

    def test_are_disks_stamped_with_current_config_false(self):
        """Test are_disks_stamped_with_current_config returns False"""
        with patch.object(handle, 'hutil', self.mock_hutil):
            mock_config = Mock()
            mock_config.get_secret_seq_num.return_value = "3"
            self.mock_hutil.get_current_seq.return_value = 5
            
            result = handle.are_disks_stamped_with_current_config(mock_config)
            self.assertFalse(result)

    def test_is_resume_phase_true(self):
        """Test is_resume_phase returns True"""
        result = handle.is_resume_phase(CommonVariables.EncryptionPhaseResume)
        self.assertTrue(result)

    def test_is_resume_phase_false(self):
        """Test is_resume_phase returns False"""
        result = handle.is_resume_phase(CommonVariables.EncryptionPhaseBackupHeader)
        self.assertFalse(result)

    @patch('handle.subprocess.Popen')
    @patch('handle.os.path.join')
    @patch('handle.os.getcwd')
    def test_is_daemon_running_true(self, mock_getcwd, mock_join, mock_popen):
        """Test is_daemon_running returns True when daemon is running"""
        mock_getcwd.return_value = '/test'
        mock_join.return_value = '/test/handle.py'
        
        mock_process = Mock()
        mock_popen.return_value = mock_process
        mock_process.communicate.return_value = (b'/test/handle.py -daemon\n', b'')
        
        result = handle.is_daemon_running()
        self.assertTrue(result)

    @patch('handle.subprocess.Popen')
    def test_is_daemon_running_false(self, mock_popen):
        """Test is_daemon_running returns False when daemon is not running"""
        mock_process = Mock()
        mock_popen.return_value = mock_process
        mock_process.communicate.return_value = (b'other process\n', b'')
        
        result = handle.is_daemon_running()
        self.assertFalse(result)

class TestHandleEncryptionFunctions(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_hutil = Mock()
        self.mock_logger = Mock()
        self.mock_encryption_environment = Mock()
        self.mock_distro_patcher = Mock()
        
        # Set up mock attributes
        self.mock_distro_patcher.distro_info = ['ubuntu', '18.04']
        self.mock_distro_patcher.support_online_encryption = True

    def test_should_perform_online_encryption_true(self):
        """Test should_perform_online_encryption returns True"""
        with patch.object(handle, 'DistroPatcher', self.mock_distro_patcher), \
             patch.object(handle, 'security_Type', CommonVariables.ConfidentialVM):
            
            mock_disk_util = Mock()
            mock_disk_util.get_luks_header_size.return_value = CommonVariables.luks_header_size_v2
            self.mock_distro_patcher.validate_online_encryption_support.return_value = True
            self.mock_distro_patcher.install_cryptsetup.return_value = None
            
            result = handle.should_perform_online_encryption(
                mock_disk_util, 
                CommonVariables.EnableEncryption, 
                CommonVariables.VolumeTypeData
            )
            self.assertTrue(result)

    def test_should_perform_online_encryption_false(self):
        """Test should_perform_online_encryption returns False"""
        with patch.object(handle, 'DistroPatcher', self.mock_distro_patcher), \
             patch.object(handle, 'security_Type', CommonVariables.Standard):
            
            mock_disk_util = Mock()
            mock_disk_util.get_luks_header_size.return_value = CommonVariables.luks_header_size_v2
            self.mock_distro_patcher.support_online_encryption = False
            
            result = handle.should_perform_online_encryption(
                mock_disk_util, 
                CommonVariables.EnableEncryption, 
                CommonVariables.VolumeTypeOS
            )
            self.assertFalse(result)

    def test_is_confidential_temp_disk_encryption_true(self):
        """Test is_confidential_temp_disk_encryption returns True"""
        with patch.object(handle, 'security_Type', CommonVariables.ConfidentialVM), \
             patch.object(handle, 'hutil', self.mock_hutil), \
             patch.object(handle, 'logger', self.mock_logger):
            
            # Set up the mock hutil context for get_public_settings
            self.mock_hutil._context._config = {
                'runtimeSettings': [{'handlerSettings': {'publicSettings': {"NoConfidentialEncryptionTempDisk": False}}}]
            }
            
            result = handle.is_confidential_temp_disk_encryption()
            self.assertTrue(result)

    def test_is_confidential_temp_disk_encryption_false(self):
        """Test is_confidential_temp_disk_encryption returns False"""
        with patch.object(handle, 'security_Type', CommonVariables.ConfidentialVM), \
             patch.object(handle, 'hutil', self.mock_hutil), \
             patch.object(handle, 'logger', self.mock_logger):
            
            # Set up the mock hutil context for get_public_settings with True flag to disable encryption
            self.mock_hutil._context._config = {
                'runtimeSettings': [{'handlerSettings': {'publicSettings': {"NoConfidentialEncryptionTempDisk": True}}}]
            }
            
            result = handle.is_confidential_temp_disk_encryption()
            self.assertFalse(result)

class TestHandleUtilityFunctions(unittest.TestCase):
    """Test cases for low-level utility functions that don't require complex mocking"""
    
    def test_none_or_empty_variations(self):
        """Test none_or_empty function with various inputs"""
        # Test with None
        self.assertTrue(handle.none_or_empty(None))
        
        # Test with empty string
        self.assertTrue(handle.none_or_empty(""))
        
        # Test with whitespace-only string
        self.assertFalse(handle.none_or_empty("   "))
        
        # Test with actual value
        self.assertFalse(handle.none_or_empty("test"))
        
        # Test with number
        self.assertFalse(handle.none_or_empty(0))
        
        # Test with boolean
        self.assertFalse(handle.none_or_empty(False))

    def test_is_resume_phase_variations(self):
        """Test is_resume_phase function with various inputs"""
        # Test with correct resume phase
        self.assertTrue(handle.is_resume_phase(CommonVariables.EncryptionPhaseResume))
        
        # Test with other phases
        self.assertFalse(handle.is_resume_phase(CommonVariables.EncryptionPhaseBackupHeader))
        self.assertFalse(handle.is_resume_phase(CommonVariables.EncryptionPhaseCopyData))
        self.assertFalse(handle.is_resume_phase(CommonVariables.EncryptionPhaseEncryptDevice))
        
        # Test with None
        self.assertFalse(handle.is_resume_phase(None))
        
        # Test with invalid string
        self.assertFalse(handle.is_resume_phase("invalid"))

    def test_not_support_header_option_distro_comprehensive(self):
        """Test not_support_header_option_distro function comprehensively"""
        # Test CentOS 6 versions
        mock_patcher = Mock()
        mock_patcher.distro_info = ['centos', '6.5']
        self.assertTrue(handle.not_support_header_option_distro(mock_patcher))
        
        mock_patcher.distro_info = ['centos', '6.9']
        self.assertTrue(handle.not_support_header_option_distro(mock_patcher))
        
        # Test RedHat 6 versions
        mock_patcher.distro_info = ['redhat', '6.8']
        self.assertTrue(handle.not_support_header_option_distro(mock_patcher))
        
        # Test SUSE 11 versions
        mock_patcher.distro_info = ['suse', '11.4']
        self.assertTrue(handle.not_support_header_option_distro(mock_patcher))
        
        # Test supported distributions
        mock_patcher.distro_info = ['ubuntu', '18.04']
        self.assertFalse(handle.not_support_header_option_distro(mock_patcher))
        
        mock_patcher.distro_info = ['centos', '7.5']
        self.assertFalse(handle.not_support_header_option_distro(mock_patcher))
        
        mock_patcher.distro_info = ['redhat', '7.8']
        self.assertFalse(handle.not_support_header_option_distro(mock_patcher))

if __name__ == '__main__':
    unittest.main()
