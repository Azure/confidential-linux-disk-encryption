#!/usr/bin/env python

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock, call

# Add the parent directory to the path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock the waagent loading to avoid Windows compatibility issues
with patch('sys.modules', {'waagent': Mock()}):
    import handle
from Common import CommonVariables


class TestHandleFunctions(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_hutil = Mock()
        self.mock_logger = Mock()
        self.mock_encryption_environment = Mock()
        
        # Patch global variables
        patcher_hutil = patch('handle.hutil', self.mock_hutil)
        patcher_logger = patch('handle.logger', self.mock_logger)
        patcher_encryption_env = patch('handle.encryption_environment', self.mock_encryption_environment)
        
        self.addCleanup(patcher_hutil.stop)
        self.addCleanup(patcher_logger.stop)
        self.addCleanup(patcher_encryption_env.stop)
        
        patcher_hutil.start()
        patcher_logger.start()
        patcher_encryption_env.start()

    def test_install(self):
        """Test install function"""
        handle.install()
        
        self.mock_hutil.do_parse_context.assert_called_once_with('Install')
        self.mock_hutil.do_exit.assert_called_once_with(
            0, 'Install', CommonVariables.extension_success_status, 
            str(CommonVariables.success), 'Install Succeeded'
        )

    def test_disable(self):
        """Test disable function"""
        with patch('handle.security_Type', CommonVariables.ConfidentialVM):
            handle.disable()
            
        self.mock_hutil.do_parse_context.assert_called_once_with('Disable')
        self.mock_hutil.archive_old_configs.assert_called_once()
        self.mock_hutil.do_exit.assert_called_once_with(
            0, 'Disable', CommonVariables.extension_success_status, '0', 'Disable succeeded'
        )

    def test_uninstall(self):
        """Test uninstall function"""
        with patch('handle.security_Type', CommonVariables.ConfidentialVM):
            handle.uninstall()
            
        self.mock_hutil.do_parse_context.assert_called_once_with('Uninstall')
        self.mock_hutil.do_exit.assert_called_once_with(
            0, 'Uninstall', CommonVariables.extension_success_status, '0', 'Uninstall succeeded'
        )

    @patch('handle.DecryptionMarkConfig')
    @patch('handle.vns_call', False)
    def test_disable_encryption(self, mock_decryption_config):
        """Test disable_encryption function"""
        mock_decryption_marker = Mock()
        mock_decryption_config.return_value = mock_decryption_marker
        
        try:
            handle.disable_encryption()
        except SystemExit:
            pass  # Expected due to exit call
            
        self.mock_hutil.do_parse_context.assert_called_once_with('DisableEncryption')
        self.mock_logger.log.assert_called_with('Disabling encryption')

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

    @patch('handle.sys.argv', ['script.py', '--vns'])
    def test_is_vns_call_true(self):
        """Test is_vns_call returns True when VNS call"""
        result = handle.is_vns_call()
        self.assertTrue(result)

    @patch('handle.DistroPatcher')
    def test_not_support_header_option_distro_centos6(self, mock_patcher):
        """Test not_support_header_option_distro for CentOS 6"""
        mock_patcher.distro_info = ['centos', '6.5']
        result = handle.not_support_header_option_distro(mock_patcher)
        self.assertTrue(result)

    @patch('handle.DistroPatcher')
    def test_not_support_header_option_distro_redhat6(self, mock_patcher):
        """Test not_support_header_option_distro for RedHat 6"""
        mock_patcher.distro_info = ['redhat', '6.8']
        result = handle.not_support_header_option_distro(mock_patcher)
        self.assertTrue(result)

    @patch('handle.DistroPatcher')
    def test_not_support_header_option_distro_suse11(self, mock_patcher):
        """Test not_support_header_option_distro for SUSE 11"""
        mock_patcher.distro_info = ['suse', '11.4']
        result = handle.not_support_header_option_distro(mock_patcher)
        self.assertTrue(result)

    @patch('handle.DistroPatcher')
    def test_not_support_header_option_distro_ubuntu(self, mock_patcher):
        """Test not_support_header_option_distro for supported distro"""
        mock_patcher.distro_info = ['ubuntu', '18.04']
        result = handle.not_support_header_option_distro(mock_patcher)
        self.assertFalse(result)

    @patch('handle.DistroPatcher')
    def test_toggle_se_linux_for_centos7_true(self, mock_patcher):
        """Test toggle_se_linux_for_centos7 for CentOS 7.0"""
        mock_patcher.distro_info = ['centos', '7.0.1']
        result = handle.toggle_se_linux_for_centos7(True)
        self.assertTrue(result)

    @patch('handle.DistroPatcher')
    def test_toggle_se_linux_for_centos7_false(self, mock_patcher):
        """Test toggle_se_linux_for_centos7 for non-CentOS 7.0"""
        mock_patcher.distro_info = ['ubuntu', '18.04']
        result = handle.toggle_se_linux_for_centos7(True)
        self.assertFalse(result)

    def test_get_public_settings_string(self):
        """Test get_public_settings when settings is a string"""
        settings_str = '{"VolumeType": "All"}'
        self.mock_hutil._context._config = {
            'runtimeSettings': [{'handlerSettings': {'publicSettings': settings_str}}]
        }
        
        with patch('json.loads') as mock_json:
            mock_json.return_value = {"VolumeType": "All"}
            result = handle.get_public_settings()
            mock_json.assert_called_once_with(settings_str)

    def test_get_public_settings_dict(self):
        """Test get_public_settings when settings is already a dict"""
        settings_dict = {"VolumeType": "All"}
        self.mock_hutil._context._config = {
            'runtimeSettings': [{'handlerSettings': {'publicSettings': settings_dict}}]
        }
        
        result = handle.get_public_settings()
        self.assertEqual(result, settings_dict)

    def test_get_protected_settings_string(self):
        """Test get_protected_settings when settings is a string"""
        settings_str = '{"Passphrase": "secret"}'
        self.mock_hutil._context._config = {
            'runtimeSettings': [{'handlerSettings': {'protectedSettings': settings_str}}]
        }
        
        with patch('json.loads') as mock_json:
            mock_json.return_value = {"Passphrase": "secret"}
            result = handle.get_protected_settings()
            mock_json.assert_called_once_with(settings_str)

    def test_get_protected_settings_dict(self):
        """Test get_protected_settings when settings is already a dict"""
        settings_dict = {"Passphrase": "secret"}
        self.mock_hutil._context._config = {
            'runtimeSettings': [{'handlerSettings': {'protectedSettings': settings_dict}}]
        }
        
        result = handle.get_protected_settings()
        self.assertEqual(result, settings_dict)

    @patch('handle.EncryptionConfig')
    def test_are_disks_stamped_with_current_config_true(self, mock_encryption_config):
        """Test are_disks_stamped_with_current_config returns True"""
        mock_config = Mock()
        mock_config.get_secret_seq_num.return_value = "5"
        mock_encryption_config.return_value = mock_config
        self.mock_hutil.get_current_seq.return_value = 5
        
        result = handle.are_disks_stamped_with_current_config(mock_config)
        self.assertTrue(result)

    @patch('handle.EncryptionConfig')
    def test_are_disks_stamped_with_current_config_false(self, mock_encryption_config):
        """Test are_disks_stamped_with_current_config returns False"""
        mock_config = Mock()
        mock_config.get_secret_seq_num.return_value = "3"
        mock_encryption_config.return_value = mock_config
        self.mock_hutil.get_current_seq.return_value = 5
        
        result = handle.are_disks_stamped_with_current_config(mock_config)
        self.assertFalse(result)

    def test_is_resume_phase_true(self):
        """Test is_resume_phase returns True"""
        result = handle.is_resume_phase(CommonVariables.EncryptionPhaseResume)
        self.assertTrue(result)

    def test_is_resume_phase_false(self):
        """Test is_resume_phase returns False"""
        result = handle.is_resume_phase(CommonVariables.EncryptionPhaseStart)
        self.assertFalse(result)

    @patch('handle.CommandExecutor')
    def test_is_daemon_running_true(self, mock_executor_class):
        """Test is_daemon_running returns True when daemon is running"""
        mock_executor = Mock()
        mock_executor_class.return_value = mock_executor
        mock_executor.Execute.return_value = CommonVariables.success
        
        result = handle.is_daemon_running()
        self.assertTrue(result)

    @patch('handle.CommandExecutor')
    def test_is_daemon_running_false(self, mock_executor_class):
        """Test is_daemon_running returns False when daemon is not running"""
        mock_executor = Mock()
        mock_executor_class.return_value = mock_executor
        mock_executor.Execute.return_value = CommonVariables.process_success + 1
        
        result = handle.is_daemon_running()
        self.assertFalse(result)


class TestHandleEncryptionFunctions(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_hutil = Mock()
        self.mock_logger = Mock()
        self.mock_encryption_environment = Mock()
        
        # Patch global variables
        patcher_hutil = patch('handle.hutil', self.mock_hutil)
        patcher_logger = patch('handle.logger', self.mock_logger)
        patcher_encryption_env = patch('handle.encryption_environment', self.mock_encryption_environment)
        
        self.addCleanup(patcher_hutil.stop)
        self.addCleanup(patcher_logger.stop)
        self.addCleanup(patcher_encryption_env.stop)
        
        patcher_hutil.start()
        patcher_logger.start()
        patcher_encryption_env.start()

    @patch('handle.DiskUtil')
    def test_should_perform_online_encryption_true(self, mock_disk_util_class):
        """Test should_perform_online_encryption returns True"""
        mock_disk_util = Mock()
        mock_disk_util_class.return_value = mock_disk_util
        mock_disk_util.should_use_azure_crypt_mount.return_value = True
        
        result = handle.should_perform_online_encryption(
            mock_disk_util, 
            CommonVariables.EnableEncryption, 
            CommonVariables.VolumeTypeData
        )
        self.assertTrue(result)

    @patch('handle.DiskUtil')
    def test_should_perform_online_encryption_false(self, mock_disk_util_class):
        """Test should_perform_online_encryption returns False"""
        mock_disk_util = Mock()
        mock_disk_util_class.return_value = mock_disk_util
        mock_disk_util.should_use_azure_crypt_mount.return_value = False
        
        result = handle.should_perform_online_encryption(
            mock_disk_util, 
            CommonVariables.EnableEncryption, 
            CommonVariables.VolumeTypeOS
        )
        self.assertFalse(result)

    def test_is_confidential_temp_disk_encryption_true(self):
        """Test is_confidential_temp_disk_encryption returns True"""
        with patch('handle.security_Type', CommonVariables.ConfidentialVM):
            with patch('handle.get_public_settings') as mock_get_settings:
                mock_get_settings.return_value = {CommonVariables.VolumeTypeKey: CommonVariables.VolumeTypeData}
                result = handle.is_confidential_temp_disk_encryption()
                self.assertTrue(result)

    def test_is_confidential_temp_disk_encryption_false(self):
        """Test is_confidential_temp_disk_encryption returns False"""
        with patch('handle.security_Type', CommonVariables.StandardVM):
            result = handle.is_confidential_temp_disk_encryption()
            self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
