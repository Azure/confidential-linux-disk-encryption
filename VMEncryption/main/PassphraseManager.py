#!/usr/bin/env python
#
# Azure Disk Encryption For Linux extension
#
# Copyright 2016 Microsoft Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import base64
import tempfile
import shutil
from Common import CommonVariables

class PassphraseManager:
    """
    Hybrid passphrase management utility that provides persistent storage
    while maintaining security benefits of BEK removal.
    """
    
    def __init__(self, logger, encryption_environment):
        self.logger = logger
        self.encryption_environment = encryption_environment
        self.passphrase_dir = "/var/lib/azure_disk_encryption"
        self._ensure_passphrase_dir()
    
    def _ensure_passphrase_dir(self):
        """Ensure the passphrase directory exists with proper permissions"""
        try:
            os.makedirs(self.passphrase_dir, mode=0o700, exist_ok=True)
            if self.logger:
                self.logger.log(f"Passphrase directory ensured: {self.passphrase_dir}")
        except Exception as e:
            if self.logger:
                self.logger.log(f"Failed to create passphrase directory: {e}", level=CommonVariables.ErrorLevel)
            raise
    
    def generate_passphrase(self):
        """Generate a random passphrase"""
        try:
            with open("/dev/urandom", "rb") as _random_source:
                bytes = _random_source.read(CommonVariables.PassphraseLengthInBytes)
                passphrase_generated = base64.b64encode(bytes)
            return passphrase_generated
        except Exception as e:
            self.logger.log(f"Failed to generate passphrase: {e}", level=CommonVariables.ErrorLevel)
            raise
    
    def get_or_generate_passphrase(self, volume_id):
        """
        Get existing passphrase for a volume or generate a new one.
        This is the core hybrid approach method.
        """
        passphrase_file = os.path.join(self.passphrase_dir, f"{volume_id}.key")
        
        try:
            if os.path.exists(passphrase_file):
                # Use existing passphrase
                if self.logger:
                    self.logger.log(f"Using existing passphrase for volume: {volume_id}")
                with open(passphrase_file, 'rb') as f:
                    return f.read()
            else:
                # Generate new passphrase and store it
                if self.logger:
                    self.logger.log(f"Generating new passphrase for volume: {volume_id}")
                passphrase = self.generate_passphrase()
                
                # Store passphrase securely
                with open(passphrase_file, 'wb') as f:
                    f.write(passphrase)
                
                # Set restrictive permissions
                os.chmod(passphrase_file, 0o600)
                
                if self.logger:
                    self.logger.log(f"Passphrase stored for volume: {volume_id}")
                return passphrase
                
        except Exception as e:
            if self.logger:
                self.logger.log(f"Failed to get/generate passphrase for {volume_id}: {e}", level=CommonVariables.ErrorLevel)
            raise
    
    def create_temp_passphrase_file(self, volume_id):
        """
        Create a temporary file with the passphrase for cryptsetup.
        This maintains compatibility with existing cryptsetup calls.
        """
        try:
            passphrase = self.get_or_generate_passphrase(volume_id)
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_file.write(passphrase)
            temp_file.close()
            
            # Set restrictive permissions
            os.chmod(temp_file.name, 0o600)
            
            if self.logger:
                self.logger.log(f"Temporary passphrase file created: {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            if self.logger:
                self.logger.log(f"Failed to create temp passphrase file for {volume_id}: {e}", level=CommonVariables.ErrorLevel)
            raise
    
    def cleanup_temp_file(self, temp_file_path):
        """Clean up temporary passphrase file"""
        try:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                if self.logger:
                    self.logger.log(f"Temporary passphrase file cleaned up: {temp_file_path}")
        except Exception as e:
            if self.logger:
                self.logger.log(f"Failed to cleanup temp file {temp_file_path}: {e}", level=CommonVariables.WarningLevel)
    
    def remove_passphrase(self, volume_id):
        """Remove stored passphrase for a volume"""
        try:
            passphrase_file = os.path.join(self.passphrase_dir, f"{volume_id}.key")
            if os.path.exists(passphrase_file):
                os.unlink(passphrase_file)
                if self.logger:
                    self.logger.log(f"Passphrase removed for volume: {volume_id}")
        except Exception as e:
            if self.logger:
                self.logger.log(f"Failed to remove passphrase for {volume_id}: {e}", level=CommonVariables.WarningLevel)
    
    def list_stored_passphrases(self):
        """List all stored passphrases (for debugging)"""
        try:
            if os.path.exists(self.passphrase_dir):
                files = [f for f in os.listdir(self.passphrase_dir) if f.endswith('.key')]
                if self.logger:
                    self.logger.log(f"Stored passphrases: {files}")
                return files
            return []
        except Exception as e:
            if self.logger:
                self.logger.log(f"Failed to list stored passphrases: {e}", level=CommonVariables.WarningLevel)
            return []
    
    def get_passphrase_file_path(self, volume_id):
        """Get the path to the stored passphrase file"""
        # Use forward slashes for Linux-only codebase
        return f"{self.passphrase_dir}/{volume_id}.key"
    
    def has_passphrase(self, volume_id):
        """Check if a passphrase exists for a volume"""
        passphrase_file = os.path.join(self.passphrase_dir, f"{volume_id}.key")
        return os.path.exists(passphrase_file)
