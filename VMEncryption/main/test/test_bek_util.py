import unittest
try:
    import unittest.mock as mock  # python 3+
except ImportError:
    import mock  # python2

from BekUtil import BekUtil
from AbstractBekUtilImpl import BekMissingException,AbstractBekUtilImpl
from DiskUtil import DiskUtil
from Common import CommonVariables
from console_logger import ConsoleLogger

class Test_Bek_Util(unittest.TestCase):
    def setUp(self):
        self.logger = ConsoleLogger()

    @mock.patch('os.path.exists')
    @mock.patch('os.path.isdir')
    @mock.patch('DiskUtil.DiskUtil', autospec=True)
    def test_is_bek_volume_mounted_and_formatted_expected(self, disk_util_mock, isdir_mock, exists_mock):
        bek_util = BekUtil(disk_util_mock, self.logger)
        # For file-based implementation, mock keyfile directory as existing and accessible
        exists_mock.return_value = True
        isdir_mock.return_value = True
        bek_expected, fault_reason = bek_util.is_bek_volume_mounted_and_formatted()
        self.assertTrue(bek_expected)

    @mock.patch('os.path.exists')
    @mock.patch('os.path.isdir')
    @mock.patch('DiskUtil.DiskUtil', autospec=True)
    def test_is_bek_volume_mounted_and_formatted_not_mounted(self, disk_util_mock, isdir_mock, exists_mock):
        bek_util = BekUtil(disk_util_mock, self.logger)
        # For file-based implementation, mock keyfile directory as not existing
        exists_mock.return_value = False
        isdir_mock.return_value = False
        bek_expected, fault_reason = bek_util.is_bek_volume_mounted_and_formatted()
        self.assertFalse(bek_expected)

    @mock.patch('os.path.exists')
    @mock.patch('os.path.isdir')
    @mock.patch('DiskUtil.DiskUtil', autospec=True)
    def test_is_bek_volume_mounted_and_formatted_wrong_fs(self, disk_util_mock, isdir_mock, exists_mock):
        bek_util = BekUtil(disk_util_mock, self.logger)
        # For file-based implementation, mock directory existing but not accessible
        exists_mock.return_value = True
        isdir_mock.return_value = False  # Exists but not a directory
        bek_expected, fault_reason = bek_util.is_bek_volume_mounted_and_formatted()
        self.assertFalse(bek_expected)

    @mock.patch('os.path.exists')
    @mock.patch('os.path.isdir')
    @mock.patch('DiskUtil.DiskUtil', autospec=True)
    def test_is_bek_disk_attached_and_partitioned_expected_gen1(self, disk_util_mock, isdir_mock, exists_mock):
        bek_util = BekUtil(disk_util_mock, self.logger)
        # For file-based implementation, directory is created successfully
        exists_mock.return_value = True
        isdir_mock.return_value = True
        bek_attached, error_reason = bek_util.is_bek_disk_attached_and_partitioned()
        self.assertTrue(bek_attached)

    @mock.patch('os.path.exists')
    @mock.patch('os.path.isdir')
    @mock.patch('DiskUtil.DiskUtil', autospec=True)
    def test_is_bek_disk_attached_and_partitioned_not_attached_gen1(self, disk_util_mock, isdir_mock, exists_mock):
        bek_util = BekUtil(disk_util_mock, self.logger)
        # Mock make_sure_path_exists to fail
        disk_util_mock.make_sure_path_exists.side_effect = Exception("Cannot create directory")
        bek_attached, error_reason = bek_util.is_bek_disk_attached_and_partitioned()
        self.assertFalse(bek_attached)

    @mock.patch('os.path.exists')
    @mock.patch('os.path.isdir')
    @mock.patch('DiskUtil.DiskUtil', autospec=True)
    def test_is_bek_disk_attached_and_partitioned_not_partitioned_gen1(self, disk_util_mock, isdir_mock, exists_mock):
        bek_util = BekUtil(disk_util_mock, self.logger)
        # Directory exists but is not accessible as a directory
        exists_mock.return_value = True
        isdir_mock.return_value = False
        bek_attached, error_reason = bek_util.is_bek_disk_attached_and_partitioned()
        self.assertFalse(bek_attached)

    @mock.patch('os.path.exists')
    @mock.patch('os.path.isdir')
    @mock.patch('DiskUtil.DiskUtil', autospec=True)
    def test_is_bek_disk_attached_and_partitioned_expected_gen2(self, disk_util_mock, isdir_mock, exists_mock):
        bek_util = BekUtil(disk_util_mock, self.logger)
        # For file-based implementation, directory is created successfully
        exists_mock.return_value = True
        isdir_mock.return_value = True
        bek_attached, error_reason = bek_util.is_bek_disk_attached_and_partitioned()
        self.assertTrue(bek_attached)

    @mock.patch('os.path.exists')
    @mock.patch('os.path.isdir')
    @mock.patch('DiskUtil.DiskUtil', autospec=True)
    def test_is_bek_disk_attached_and_partitioned_not_attached_gen2(self, disk_util_mock, isdir_mock, exists_mock):
        bek_util = BekUtil(disk_util_mock, self.logger)
        # Mock make_sure_path_exists to fail
        disk_util_mock.make_sure_path_exists.side_effect = Exception("Cannot create directory")
        bek_attached, error_reason = bek_util.is_bek_disk_attached_and_partitioned()
        self.assertFalse(bek_attached)

    @mock.patch('os.path.exists')
    @mock.patch('os.path.isdir')
    @mock.patch('DiskUtil.DiskUtil', autospec=True)
    def test_is_bek_disk_attached_and_partitioned_not_partitioned_gen2(self, disk_util_mock, isdir_mock, exists_mock):
        bek_util = BekUtil(disk_util_mock, self.logger)
        # Directory exists but is not accessible as a directory
        exists_mock.return_value = True
        isdir_mock.return_value = False
        bek_attached, error_reason = bek_util.is_bek_disk_attached_and_partitioned()
        self.assertFalse(bek_attached)

    
