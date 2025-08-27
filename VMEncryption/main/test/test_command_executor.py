import unittest
import platform
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from subprocess import Popen, PIPE

# Add the test directory to path for console_logger import
sys.path.insert(0, os.path.dirname(__file__))

from CommandExecutor import CommandExecutor, ProcessCommunicator
from console_logger import ConsoleLogger

class TestCommandExecutor(unittest.TestCase):
    """ unit tests for functions in the CommandExecutor module """
    def setUp(self):
        self.logger = ConsoleLogger()
        self.cmd_executor = CommandExecutor(self.logger)
        
        # Use appropriate sleep command for the platform
        if platform.system() == 'Windows':
            # Use a simple Windows command that should always succeed
            self.sleep_cmd_short = 'cmd /c echo test'
            # Use timeout command for long operations
            self.sleep_cmd_long = 'timeout /t 15 /nobreak'
        else:
            self.sleep_cmd_short = 'sleep 1'  # Reduced to 1 second for faster tests
            self.sleep_cmd_long = 'sleep 15'

    def test_command_timeout(self):
        # Skip timeout test on Windows as it's unreliable
        if platform.system() == 'Windows':
            self.skipTest("Timeout test unreliable on Windows")
        return_code = self.cmd_executor.Execute(self.sleep_cmd_long, timeout=5)
        # On Windows, the return code may not be exactly -9, but should be negative
        self.assertLess(return_code, 0, msg="The command didn't timeout as expected")

    def test_command_no_timeout(self):
        return_code = self.cmd_executor.Execute(self.sleep_cmd_short, timeout=10)
        self.assertEqual(return_code, 0, msg="The command should have completed successfully")

    def test_get_text_with_string(self):
        """Test get_text with string input."""
        result = self.cmd_executor.get_text("test string")
        self.assertEqual(result, "test string")

    def test_get_text_with_bytes(self):
        """Test get_text with bytes input."""
        test_bytes = b"test bytes"
        result = self.cmd_executor.get_text(test_bytes)
        self.assertEqual(result, "test bytes")

    @patch('CommandExecutor.Popen')
    def test_execute_successful_command(self, mock_popen):
        """Test successful command execution."""
        mock_process = Mock()
        mock_process.communicate.return_value = (b"stdout output", b"")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        result = self.cmd_executor.Execute("echo test")
        
        self.assertEqual(result, 0)
        mock_popen.assert_called_once()

    @patch('CommandExecutor.Popen')
    def test_execute_failed_command(self, mock_popen):
        """Test failed command execution."""
        mock_process = Mock()
        mock_process.communicate.return_value = (b"", b"error output")
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        result = self.cmd_executor.Execute("false command")
        
        self.assertEqual(result, 1)

    @patch('CommandExecutor.Popen')
    def test_execute_with_exception_raising(self, mock_popen):
        """Test command execution with exception raising enabled."""
        mock_process = Mock()
        mock_process.communicate.return_value = (b"", b"error output")
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        with self.assertRaises(Exception):
            self.cmd_executor.Execute("false command", raise_exception_on_failure=True)

    @patch('CommandExecutor.Popen')
    def test_execute_with_communicator(self, mock_popen):
        """Test command execution with ProcessCommunicator."""
        mock_process = Mock()
        mock_process.communicate.return_value = (b"stdout output", b"stderr output")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        communicator = ProcessCommunicator()
        result = self.cmd_executor.Execute("echo test", communicator=communicator)
        
        self.assertEqual(result, 0)
        self.assertEqual(communicator.stdout, "stdout output")
        self.assertEqual(communicator.stderr, "stderr output")

    @patch('CommandExecutor.Popen')
    def test_execute_with_input(self, mock_popen):
        """Test command execution with input."""
        mock_process = Mock()
        mock_process.communicate.return_value = (b"output", b"")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        result = self.cmd_executor.Execute("cat", input=b"test input")
        
        self.assertEqual(result, 0)
        mock_process.communicate.assert_called_with(input=b"test input")

    @patch('CommandExecutor.Popen')
    def test_execute_with_suppress_logging(self, mock_popen):
        """Test command execution with logging suppressed."""
        mock_process = Mock()
        mock_process.communicate.return_value = (b"output", b"")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        mock_logger = Mock()
        cmd_executor = CommandExecutor(mock_logger)
        
        result = cmd_executor.Execute("echo test", suppress_logging=True)
        
        self.assertEqual(result, 0)
        mock_logger.log.assert_not_called()

    @patch('CommandExecutor.Popen')
    def test_execute_process_creation_failure(self, mock_popen):
        """Test handling of process creation failure."""
        mock_popen.side_effect = OSError("Process creation failed")

        result = self.cmd_executor.Execute("invalid command")
        
        self.assertEqual(result, -1)

    @patch('CommandExecutor.Popen')
    def test_execute_process_creation_failure_with_exception(self, mock_popen):
        """Test handling of process creation failure with exception raising."""
        mock_popen.side_effect = OSError("Process creation failed")

        with self.assertRaises(OSError):
            self.cmd_executor.Execute("invalid command", raise_exception_on_failure=True)

    @patch('CommandExecutor.Timer')
    @patch('CommandExecutor.Popen')
    def test_execute_with_timeout_success(self, mock_popen, mock_timer):
        """Test command execution with timeout that completes successfully."""
        mock_process = Mock()
        mock_process.communicate.return_value = (b"output", b"")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        
        mock_timer_instance = Mock()
        mock_timer.return_value = mock_timer_instance

        result = self.cmd_executor.Execute("echo test", timeout=5)
        
        self.assertEqual(result, 0)
        mock_timer.assert_called_once()
        mock_timer_instance.start.assert_called_once()
        mock_timer_instance.cancel.assert_called_once()

    def test_execute_in_bash_success(self):
        """Test ExecuteInBash with successful command."""
        with patch.object(self.cmd_executor, 'Execute') as mock_execute:
            mock_execute.return_value = 0
            
            result = self.cmd_executor.ExecuteInBash("echo test")
            
            self.assertEqual(result, 0)
            mock_execute.assert_called_once()
            # Check that the command was wrapped in bash
            args, kwargs = mock_execute.call_args
            self.assertIn('bash -c', args[0])

    def test_execute_in_bash_with_exception_raising(self):
        """Test ExecuteInBash with exception raising enabled."""
        with patch.object(self.cmd_executor, 'Execute') as mock_execute:
            mock_execute.return_value = 0
            
            result = self.cmd_executor.ExecuteInBash("echo test", raise_exception_on_failure=True)
            
            self.assertEqual(result, 0)
            # Check that 'set -e' was added to the command
            args, kwargs = mock_execute.call_args
            self.assertIn('set -e', args[0])

    def test_execute_in_bash_parameters_passed(self):
        """Test that ExecuteInBash passes all parameters correctly."""
        communicator = ProcessCommunicator()
        
        with patch.object(self.cmd_executor, 'Execute') as mock_execute:
            mock_execute.return_value = 0
            
            self.cmd_executor.ExecuteInBash(
                "echo test", 
                raise_exception_on_failure=True,
                communicator=communicator,
                input=b"test input",
                suppress_logging=True
            )
            
            mock_execute.assert_called_once()
            args, kwargs = mock_execute.call_args
            # ExecuteInBash passes parameters as positional arguments to Execute
            self.assertEqual(args[1], True)  # raise_exception_on_failure
            self.assertEqual(args[2], communicator)  # communicator
            self.assertEqual(args[3], b"test input")  # input
            self.assertEqual(args[4], True)  # suppress_logging