import unittest
import platform
import sys
import os

# Add the test directory to path for console_logger import
sys.path.insert(0, os.path.dirname(__file__))

from CommandExecutor import CommandExecutor
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