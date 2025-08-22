import unittest
import sys
import os
from unittest.mock import Mock, patch

# Add the test directory to path for console_logger import
sys.path.insert(0, os.path.dirname(__file__))

from ProcessLock import ProcessLock
from console_logger import ConsoleLogger

class TestProcessLock(unittest.TestCase):
    """Unit tests for ProcessLock class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.logger = ConsoleLogger()
        self.lock_file_path = "/tmp/test_lock.lock"
        
    def test_init(self):
        """Test ProcessLock initialization."""
        process_lock = ProcessLock(self.logger, self.lock_file_path)
        
        self.assertEqual(process_lock.logger, self.logger)
        self.assertEqual(process_lock.lock_file_path, self.lock_file_path)
        self.assertIsNone(process_lock.fd)

    @patch('ProcessLock.FCNTL_AVAILABLE', False)
    def test_try_lock_fcntl_not_available(self):
        """Test try_lock when fcntl is not available (Windows)."""
        mock_logger = Mock()
        process_lock = ProcessLock(mock_logger, self.lock_file_path)
        
        result = process_lock.try_lock()
        
        self.assertTrue(result)
        mock_logger.log.assert_called_once_with(
            "fcntl not available (likely Windows environment), skipping file locking"
        )

    def test_release_lock_fd_none(self):
        """Test release_lock when fd is None."""
        mock_logger = Mock()
        process_lock = ProcessLock(mock_logger, self.lock_file_path)
        
        # Should not raise exception when fd is None
        process_lock.release_lock()
        
        # No logging should occur when fd is None
        mock_logger.log.assert_not_called()

    @patch('ProcessLock.FCNTL_AVAILABLE', False)
    def test_release_lock_fcntl_not_available(self):
        """Test release_lock when fcntl is not available."""
        mock_logger = Mock()
        process_lock = ProcessLock(mock_logger, self.lock_file_path)
        mock_fd = Mock()
        process_lock.fd = mock_fd
        
        # Should return early when FCNTL_AVAILABLE is False
        process_lock.release_lock()
        
        # fd.close should not be called when FCNTL_AVAILABLE is False
        mock_fd.close.assert_not_called()


if __name__ == '__main__':
    unittest.main()
