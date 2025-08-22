#!/usr/bin/env python

import unittest
import os
import sys
import io
import string
from unittest.mock import Mock, patch, mock_open, MagicMock

# Add the main directory to the path to import the module
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from BackupLogger import BackupLogger


class TestBackupLogger(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_hutil = Mock()
        
    def test_init(self):
        """Test initialization of BackupLogger."""
        with patch('os.getpid', return_value=12345):
            logger = BackupLogger(self.mock_hutil)
            
            self.assertEqual(logger.hutil, self.mock_hutil)
            self.assertEqual(logger.current_process_id, 12345)
            
    def test_log_basic_message(self):
        """Test logging a basic message."""
        with patch('os.getpid', return_value=12345):
            with patch.object(BackupLogger, 'log_to_console') as mock_log_to_console:
                logger = BackupLogger(self.mock_hutil)
                
                logger.log("Test message", "Info")
                
                # Verify hutil.log was called
                self.mock_hutil.log.assert_called_once()
                logged_msg = self.mock_hutil.log.call_args[0][0]
                
                self.assertIn("12345", logged_msg)
                self.assertIn("[Info]", logged_msg)
                self.assertIn("Test message", logged_msg)
                
                # Verify log_to_console was called
                mock_log_to_console.assert_called_once()
                
    def test_log_default_level(self):
        """Test logging with default level."""
        with patch('os.getpid', return_value=12345):
            with patch.object(BackupLogger, 'log_to_console') as mock_log_to_console:
                logger = BackupLogger(self.mock_hutil)
                
                logger.log("Test message")  # No level specified, should default to 'Info'
                
                logged_msg = self.mock_hutil.log.call_args[0][0]
                self.assertIn("[Info]", logged_msg)
                
    def test_log_message_with_quotes(self):
        """Test logging message with double quotes that should be escaped."""
        with patch('os.getpid', return_value=12345):
            with patch.object(BackupLogger, 'log_to_console') as mock_log_to_console:
                logger = BackupLogger(self.mock_hutil)
                
                logger.log('Message with "quotes" in it', "Warning")
                
                logged_msg = self.mock_hutil.log.call_args[0][0]
                # Double quotes should be replaced with single quotes
                self.assertIn("Message with 'quotes' in it", logged_msg)
                self.assertNotIn('"', logged_msg)
                
    def test_log_message_with_non_printable_characters(self):
        """Test logging message with non-printable characters."""
        with patch('os.getpid', return_value=12345):
            with patch.object(BackupLogger, 'log_to_console') as mock_log_to_console:
                logger = BackupLogger(self.mock_hutil)
                
                # Message with some non-printable characters
                message_with_non_printable = "Valid message\x00\x01\x02invalid chars"
                logger.log(message_with_non_printable, "Error")
                
                logged_msg = self.mock_hutil.log.call_args[0][0]
                # Non-printable characters should be filtered out
                self.assertIn("Valid message", logged_msg)
                self.assertIn("invalid chars", logged_msg)
                # Verify only printable characters remain
                for char in logged_msg:
                    self.assertIn(char, string.printable)
                    
    def test_log_to_console_success(self):
        """Test successful logging to console."""
        with patch('os.getpid', return_value=12345):
            mock_file = mock_open()
            with patch('io.open', mock_file):
                logger = BackupLogger(self.mock_hutil)
                
                logger.log_to_console("Test console message")
                
                # Verify file was opened correctly
                mock_file.assert_called_once_with('/dev/console', 'w')
                
                # Verify write was called
                handle = mock_file.return_value
                handle.write.assert_called_once()
                
                # Check the written content
                written_content = handle.write.call_args[0][0]
                self.assertIn("[AzureDiskEncryption]", written_content)
                self.assertIn("Test console message", written_content)
                self.assertTrue(written_content.endswith('\n'))
                
    def test_log_to_console_io_error(self):
        """Test logging to console with IO error."""
        with patch('os.getpid', return_value=12345):
            with patch('io.open', side_effect=IOError("Permission denied")):
                logger = BackupLogger(self.mock_hutil)
                
                # Should not raise exception, just silently fail
                try:
                    logger.log_to_console("Test message")
                except IOError:
                    self.fail("log_to_console should handle IOError silently")
                    
    def test_log_to_console_with_non_printable_characters(self):
        """Test log_to_console with non-printable characters."""
        with patch('os.getpid', return_value=12345):
            mock_file = mock_open()
            with patch('io.open', mock_file):
                logger = BackupLogger(self.mock_hutil)
                
                message_with_non_printable = "Valid\x00\x01invalid"
                logger.log_to_console(message_with_non_printable)
                
                handle = mock_file.return_value
                written_content = handle.write.call_args[0][0]
                
                # Check that non-printable characters are filtered
                for char in written_content:
                    if char not in ['[', ']', '\n']:  # Allow structural characters
                        self.assertIn(char, string.printable)
                        
    def test_log_to_console_python3_unicode_handling(self):
        """Test log_to_console unicode handling for Python 3."""
        with patch('os.getpid', return_value=12345):
            with patch('sys.version_info', [3, 8, 0]):  # Simulate Python 3.x
                mock_file = mock_open()
                with patch('io.open', mock_file):
                    logger = BackupLogger(self.mock_hutil)
                    
                    test_message = "Test unicode message"
                    logger.log_to_console(test_message)
                    
                    handle = mock_file.return_value
                    handle.write.assert_called_once()
                    
                    written_content = handle.write.call_args[0][0]
                    self.assertIn("Test unicode message", written_content)
                    
    def test_complete_logging_workflow(self):
        """Test complete logging workflow from log() to console output."""
        with patch('os.getpid', return_value=54321):
            mock_file = mock_open()
            with patch('io.open', mock_file):
                logger = BackupLogger(self.mock_hutil)
                
                logger.log('Complete "test" message', "Debug")
                
                # Verify hutil.log was called with processed message
                self.mock_hutil.log.assert_called_once()
                hutil_logged_msg = self.mock_hutil.log.call_args[0][0]
                self.assertIn("54321", hutil_logged_msg)
                self.assertIn("[Debug]", hutil_logged_msg)
                self.assertIn("Complete 'test' message", hutil_logged_msg)  # Quotes replaced
                
                # Verify console logging
                mock_file.assert_called_once_with('/dev/console', 'w')
                handle = mock_file.return_value
                handle.write.assert_called_once()
                
                console_logged_msg = handle.write.call_args[0][0]
                self.assertIn("[AzureDiskEncryption]", console_logged_msg)
                self.assertIn("54321", console_logged_msg)
                self.assertIn("[Debug]", console_logged_msg)
                
    def test_multiple_log_calls(self):
        """Test multiple sequential log calls."""
        with patch('os.getpid', return_value=99999):
            mock_file = mock_open()
            with patch('io.open', mock_file):
                logger = BackupLogger(self.mock_hutil)
                
                logger.log("First message", "Info")
                logger.log("Second message", "Warning")
                logger.log("Third message", "Error")
                
                # Verify hutil.log was called 3 times
                self.assertEqual(self.mock_hutil.log.call_count, 3)
                
                # Verify console logging was attempted 3 times
                self.assertEqual(mock_file.call_count, 3)
                
                # Check content of each call
                call_args_list = self.mock_hutil.log.call_args_list
                
                self.assertIn("First message", call_args_list[0][0][0])
                self.assertIn("[Info]", call_args_list[0][0][0])
                
                self.assertIn("Second message", call_args_list[1][0][0])
                self.assertIn("[Warning]", call_args_list[1][0][0])
                
                self.assertIn("Third message", call_args_list[2][0][0])
                self.assertIn("[Error]", call_args_list[2][0][0])


if __name__ == '__main__':
    unittest.main()
