#!/usr/bin/env python

import unittest
import sys
import os

# Simple test for EncryptionEnvironment
class TestEncryptionEnvironmentSimple(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Add the main directory to the path to import the module
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        
        from unittest.mock import Mock
        self.mock_patching = Mock()
        self.mock_logger = Mock()
        self.mock_patching.getenforce_path = '/usr/sbin/getenforce'
        self.mock_patching.setenforce_path = '/usr/sbin/setenforce'
        
    def test_init(self):
        """Test initialization of EncryptionEnvironment."""
        from EncryptionEnvironment import EncryptionEnvironment
        env = EncryptionEnvironment(self.mock_patching, self.mock_logger)
        
        self.assertEqual(env.patching, self.mock_patching)
        self.assertEqual(env.logger, self.mock_logger)
        self.assertEqual(env.encryption_config_path, '/var/lib/azure_disk_encryption_config/')
        
    def test_init_default_paths(self):
        """Test initialization with default path values."""
        from EncryptionEnvironment import EncryptionEnvironment
        env = EncryptionEnvironment(self.mock_patching, self.mock_logger)
        
        # Check default paths are set
        self.assertIsNotNone(env.encryption_config_path)
        self.assertIsNotNone(env.default_bek_filename)
        self.assertEqual(env.default_bek_filename, "LinuxPassPhraseFileName")

    def test_encryption_config_path_default(self):
        """Test that default encryption config path is set correctly."""
        from EncryptionEnvironment import EncryptionEnvironment
        env = EncryptionEnvironment(self.mock_patching, self.mock_logger)
        expected_path = '/var/lib/azure_disk_encryption_config/'
        self.assertEqual(env.encryption_config_path, expected_path)

    def test_azure_crypt_mount_config_path(self):
        """Test that azure crypt mount config path is constructed correctly."""
        from EncryptionEnvironment import EncryptionEnvironment
        env = EncryptionEnvironment(self.mock_patching, self.mock_logger)
        expected_path = '/var/lib/azure_disk_encryption_config/azure_crypt_mount'
        self.assertEqual(env.azure_crypt_mount_config_path, expected_path)

    def test_default_bek_filename(self):
        """Test that default BEK filename is set correctly."""
        from EncryptionEnvironment import EncryptionEnvironment
        env = EncryptionEnvironment(self.mock_patching, self.mock_logger)
        expected_filename = "LinuxPassPhraseFileName"
        self.assertEqual(env.default_bek_filename, expected_filename)

    def test_attribute_access(self):
        """Test that all expected attributes are accessible."""
        from EncryptionEnvironment import EncryptionEnvironment
        env = EncryptionEnvironment(self.mock_patching, self.mock_logger)
        
        # Test all attributes exist and have expected types
        self.assertIsNotNone(env.patching)
        self.assertIsNotNone(env.logger)
        self.assertIsInstance(env.encryption_config_path, str)
        self.assertIsInstance(env.azure_crypt_mount_config_path, str)
        self.assertIsInstance(env.default_bek_filename, str)


if __name__ == '__main__':
    unittest.main()
