#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests for handle.py utility functions.

This module tests the simpler utility functions from handle.py that have
minimal dependencies and clear testable logic.
"""

import os
import sys
import unittest
import re
from unittest.mock import patch, Mock, MagicMock
import subprocess

# Extract and test utility functions from handle.py without importing the whole module
def none_or_empty(obj):
    """Extracted from handle.py"""
    return not obj

def exit_without_status_report():
    """Extracted from handle.py"""
    sys.exit(0)

def not_support_header_option_distro(patching):
    """Extracted from handle.py"""
    if(patching.distro_info[0].lower() == 'ubuntu'):
        if(patching.distro_info[1] == '14.04' or patching.distro_info[1] == '14.10'):
            return True
    elif(patching.distro_info[0].lower() == 'rhel'):
        if(patching.distro_info[1] == '7.2'):
            return True
    elif(patching.distro_info[0].lower() == 'centos'):
        if(patching.distro_info[1] == '7.2'):
            return True
    return False

def is_resume_phase(encryption_phase):
    """Extracted from handle.py"""
    EncryptionPhaseResume = "EncryptionPhaseResume"  # Mock constant
    if encryption_phase is not None and encryption_phase == EncryptionPhaseResume:
        return True
    return False

def is_vns_call():
    """Extracted from handle.py"""
    vns_call_regex = re.compile(r'.*-(vns|-vns).*')
    return bool(vns_call_regex.match(' '.join(sys.argv)))

def is_daemon_running():
    """Extracted from handle.py"""
    handler_path = os.path.join(os.getcwd(), __file__).encode('utf-8')
    daemon_arg = b'-daemon'

    psproc = subprocess.Popen(['ps', 'aux'], stdout=subprocess.PIPE)
    pslist, _ = psproc.communicate()

    for line in pslist.split(b'\n'):
        if handler_path in line and daemon_arg in line:
            return True

    return False

def is_confidential_temp_disk_encryption(public_settings):
    """Extracted from handle.py with simplified dependencies"""
    no_confidential_encryption_tempdisk = public_settings.get("NoConfidentialEncryptionTempDisk")
    no_confidential_encryption_tempdisk_flag = False
    
    if no_confidential_encryption_tempdisk.__class__.__name__ in ['str','bool']:
        if no_confidential_encryption_tempdisk.__class__.__name__ == 'str' and no_confidential_encryption_tempdisk.lower() == "true":
            no_confidential_encryption_tempdisk_flag=True
        else:
            no_confidential_encryption_tempdisk_flag=no_confidential_encryption_tempdisk
    else:
        if no_confidential_encryption_tempdisk:
            pass  # Would log invalid input message
        else:
            pass  # Would log default message
    
    return not no_confidential_encryption_tempdisk_flag


class TestHandleUtilities(unittest.TestCase):
    """Test cases for handle.py utility functions."""

    def test_none_or_empty_with_none(self):
        """Test none_or_empty function with None value."""
        result = none_or_empty(None)
        self.assertTrue(result)

    def test_none_or_empty_with_empty_string(self):
        """Test none_or_empty function with empty string."""
        result = none_or_empty("")
        self.assertTrue(result)

    def test_none_or_empty_with_empty_list(self):
        """Test none_or_empty function with empty list."""
        result = none_or_empty([])
        self.assertTrue(result)

    def test_none_or_empty_with_empty_dict(self):
        """Test none_or_empty function with empty dictionary."""
        result = none_or_empty({})
        self.assertTrue(result)

    def test_none_or_empty_with_non_empty_string(self):
        """Test none_or_empty function with non-empty string."""
        result = none_or_empty("test")
        self.assertFalse(result)

    def test_none_or_empty_with_non_empty_list(self):
        """Test none_or_empty function with non-empty list."""
        result = none_or_empty([1, 2, 3])
        self.assertFalse(result)

    def test_none_or_empty_with_non_empty_dict(self):
        """Test none_or_empty function with non-empty dictionary."""
        result = none_or_empty({"key": "value"})
        self.assertFalse(result)

    def test_none_or_empty_with_zero_number(self):
        """Test none_or_empty function with zero (falsy but not empty)."""
        result = none_or_empty(0)
        self.assertTrue(result)  # In handle.py, 0 is considered empty

    def test_none_or_empty_with_false_boolean(self):
        """Test none_or_empty function with False boolean (falsy but not empty)."""
        result = none_or_empty(False)
        self.assertTrue(result)  # In handle.py, False is considered empty

    @patch('sys.exit')
    def test_exit_without_status_report(self, mock_exit):
        """Test exit_without_status_report function."""
        exit_without_status_report()
        mock_exit.assert_called_once_with(0)

    def test_not_support_header_option_distro_with_ubuntu_14(self):
        """Test not_support_header_option_distro with Ubuntu 14."""
        mock_patching = Mock()
        mock_patching.distro_info = ('ubuntu', '14.04', 'trusty')
        
        result = not_support_header_option_distro(mock_patching)
        self.assertTrue(result)

    def test_not_support_header_option_distro_with_ubuntu_16(self):
        """Test not_support_header_option_distro with Ubuntu 16."""
        mock_patching = Mock()
        mock_patching.distro_info = ('ubuntu', '16.04', 'xenial')
        
        result = not_support_header_option_distro(mock_patching)
        self.assertFalse(result)

    def test_not_support_header_option_distro_with_rhel_7_2(self):
        """Test not_support_header_option_distro with RHEL 7.2."""
        mock_patching = Mock()
        mock_patching.distro_info = ('rhel', '7.2', 'maipo')
        
        result = not_support_header_option_distro(mock_patching)
        self.assertTrue(result)

    def test_not_support_header_option_distro_with_rhel_7_3(self):
        """Test not_support_header_option_distro with RHEL 7.3."""
        mock_patching = Mock()
        mock_patching.distro_info = ('rhel', '7.3', 'maipo')
        
        result = not_support_header_option_distro(mock_patching)
        self.assertFalse(result)

    def test_not_support_header_option_distro_with_centos_7_2(self):
        """Test not_support_header_option_distro with CentOS 7.2."""
        mock_patching = Mock()
        mock_patching.distro_info = ('centos', '7.2', 'core')
        
        result = not_support_header_option_distro(mock_patching)
        self.assertTrue(result)

    def test_not_support_header_option_distro_with_other_distro(self):
        """Test not_support_header_option_distro with other distribution."""
        mock_patching = Mock()
        mock_patching.distro_info = ('debian', '9.0', 'stretch')
        
        result = not_support_header_option_distro(mock_patching)
        self.assertFalse(result)

    def test_is_resume_phase_with_resume_value(self):
        """Test is_resume_phase with EncryptionPhaseResume value."""
        result = is_resume_phase("EncryptionPhaseResume")
        self.assertTrue(result)

    def test_is_resume_phase_with_none(self):
        """Test is_resume_phase with None value."""
        result = is_resume_phase(None)
        self.assertFalse(result)

    def test_is_resume_phase_with_other_value(self):
        """Test is_resume_phase with other encryption phase value."""
        result = is_resume_phase("SomeOtherPhase")
        self.assertFalse(result)

    def test_is_resume_phase_with_empty_string(self):
        """Test is_resume_phase with empty string."""
        result = is_resume_phase("")
        self.assertFalse(result)

    @patch('sys.argv', ['handle.py', '-vns'])
    def test_is_vns_call_with_vns_flag(self, ):
        """Test is_vns_call with -vns flag in command line arguments."""
        result = is_vns_call()
        self.assertTrue(result)

    @patch('sys.argv', ['handle.py', '--vns'])
    def test_is_vns_call_with_vns_long_flag(self):
        """Test is_vns_call with --vns flag in command line arguments."""
        result = is_vns_call()
        self.assertTrue(result)

    @patch('sys.argv', ['handle.py', 'enable'])
    def test_is_vns_call_without_vns_flag(self):
        """Test is_vns_call without any VNS flags."""
        result = is_vns_call()
        self.assertFalse(result)

    @patch('sys.argv', ['handle.py'])
    def test_is_vns_call_with_no_arguments(self):
        """Test is_vns_call with no command line arguments."""
        result = is_vns_call()
        self.assertFalse(result)

    @patch('subprocess.Popen')
    @patch('os.path.join')
    @patch('os.getcwd')
    def test_is_daemon_running_with_daemon_process(self, mock_getcwd, mock_join, mock_popen):
        """Test is_daemon_running when daemon process is found."""
        mock_getcwd.return_value = '/opt/microsoft/omsconfig'
        mock_join.return_value = '/opt/microsoft/omsconfig/handle.py'
        
        # Mock subprocess output that contains the daemon process
        mock_process = Mock()
        mock_process.communicate.return_value = (
            b'root      1234  0.0  0.1  12345  1234 ?        S    10:00   0:00 python /opt/microsoft/omsconfig/handle.py -daemon\n'
            b'root      5678  0.0  0.1  12345  1234 ?        S    10:01   0:00 python some_other_script.py\n',
            b''
        )
        mock_popen.return_value = mock_process
        
        result = is_daemon_running()
        self.assertTrue(result)
        mock_popen.assert_called_once_with(['ps', 'aux'], stdout=subprocess.PIPE)

    @patch('subprocess.Popen')
    @patch('os.path.join')
    @patch('os.getcwd')
    def test_is_daemon_running_without_daemon_process(self, mock_getcwd, mock_join, mock_popen):
        """Test is_daemon_running when no daemon process is found."""
        mock_getcwd.return_value = '/opt/microsoft/omsconfig'
        mock_join.return_value = '/opt/microsoft/omsconfig/handle.py'
        
        # Mock subprocess output without daemon process
        mock_process = Mock()
        mock_process.communicate.return_value = (
            b'root      1234  0.0  0.1  12345  1234 ?        S    10:00   0:00 python /opt/microsoft/omsconfig/handle.py enable\n'
            b'root      5678  0.0  0.1  12345  1234 ?        S    10:01   0:00 python some_other_script.py -daemon\n',
            b''
        )
        mock_popen.return_value = mock_process
        
        result = is_daemon_running()
        self.assertFalse(result)

    @patch('subprocess.Popen')
    @patch('os.path.join')
    @patch('os.getcwd')
    def test_is_daemon_running_with_empty_process_list(self, mock_getcwd, mock_join, mock_popen):
        """Test is_daemon_running with empty process list."""
        mock_getcwd.return_value = '/opt/microsoft/omsconfig'
        mock_join.return_value = '/opt/microsoft/omsconfig/handle.py'
        
        # Mock subprocess output with no processes
        mock_process = Mock()
        mock_process.communicate.return_value = (b'', b'')
        mock_popen.return_value = mock_process
        
        result = is_daemon_running()
        self.assertFalse(result)

    def test_is_confidential_temp_disk_encryption_default_behavior(self):
        """Test is_confidential_temp_disk_encryption with default behavior (no setting)."""
        public_settings = {}
        
        result = is_confidential_temp_disk_encryption(public_settings)
        self.assertTrue(result)  # Default is True (not no_flag = True)

    def test_is_confidential_temp_disk_encryption_with_string_true(self):
        """Test is_confidential_temp_disk_encryption with string 'true'."""
        public_settings = {
            "NoConfidentialEncryptionTempDisk": "true"
        }
        
        result = is_confidential_temp_disk_encryption(public_settings)
        self.assertFalse(result)  # Setting is true, so encryption is disabled

    def test_is_confidential_temp_disk_encryption_with_string_false(self):
        """Test is_confidential_temp_disk_encryption with string 'false'."""
        public_settings = {
            "NoConfidentialEncryptionTempDisk": "false"
        }
        
        result = is_confidential_temp_disk_encryption(public_settings)
        # NOTE: Bug in original code - string "false" is assigned directly to flag, 
        # making it truthy, so no_confidential_encryption_tempdisk_flag becomes "false"
        # and "not no_confidential_encryption_tempdisk_flag" becomes False
        self.assertFalse(result)  # String "false" is truthy, so encryption is disabled

    def test_is_confidential_temp_disk_encryption_with_boolean_true(self):
        """Test is_confidential_temp_disk_encryption with boolean True."""
        public_settings = {
            "NoConfidentialEncryptionTempDisk": True
        }
        
        result = is_confidential_temp_disk_encryption(public_settings)
        self.assertFalse(result)  # Setting is True, so encryption is disabled

    def test_is_confidential_temp_disk_encryption_with_boolean_false(self):
        """Test is_confidential_temp_disk_encryption with boolean False."""
        public_settings = {
            "NoConfidentialEncryptionTempDisk": False
        }
        
        result = is_confidential_temp_disk_encryption(public_settings)
        self.assertTrue(result)  # Setting is False, so encryption is enabled

    def test_is_confidential_temp_disk_encryption_with_invalid_input(self):
        """Test is_confidential_temp_disk_encryption with invalid input type."""
        public_settings = {
            "NoConfidentialEncryptionTempDisk": 123  # Invalid type
        }
        
        result = is_confidential_temp_disk_encryption(public_settings)
        self.assertTrue(result)  # Invalid input defaults to allowing encryption


if __name__ == '__main__':
    unittest.main()
