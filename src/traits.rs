//! Traits for dependency injection and mocking.
//!
//! This module defines traits that abstract external dependencies, making the
//! code testable with mock implementations.

use crate::disk::DiskInfo;
use crate::error::Result;

/// Trait for disk discovery operations.
///
/// This trait abstracts the disk discovery mechanism, allowing for mock
/// implementations in tests.
#[cfg_attr(test, mockall::automock)]
pub trait DiskDiscovery: Send + Sync {
    /// Discover all disks on the system.
    fn discover_disks(&self) -> Vec<DiskInfo>;
    
    /// Check if a disk is a data disk (not OS disk).
    fn is_data_disk(&self, disk: &DiskInfo) -> bool;
}

/// Trait for encryption operations.
///
/// This trait abstracts the encryption mechanism, allowing for mock
/// implementations in tests.
#[cfg_attr(test, mockall::automock)]
pub trait EncryptionProvider: Send + Sync {
    /// Check if a disk is already encrypted.
    fn is_encrypted(&self, disk: &DiskInfo) -> Result<bool>;
    
    /// Encrypt a disk with the given key.
    fn encrypt(&self, disk: &DiskInfo, key: &[u8]) -> Result<()>;
    
    /// Set up automatic unlock for a disk.
    fn setup_auto_unlock(&self, disk: &DiskInfo) -> Result<()>;
}

/// Trait for TPM operations.
///
/// This trait abstracts TPM interactions for testing.
#[cfg_attr(test, mockall::automock)]
pub trait TpmProvider: Send + Sync {
    /// Check if a TPM is available on the system.
    fn is_available(&self) -> bool;
    
    /// Enroll a disk with TPM-based auto-unlock.
    fn enroll_disk(&self, device_path: &str) -> Result<()>;
}

/// Trait for command execution.
///
/// This trait abstracts command execution for testing.
#[cfg_attr(test, mockall::automock)]
pub trait CommandRunner: Send + Sync {
    /// Check if a command exists on the system.
    fn command_exists(&self, command: &str) -> bool;
    
    /// Run a command and return its output.
    /// Args are passed as a single comma-separated string for mockall compatibility.
    fn run_command(&self, command: &str, args: Vec<String>) -> Result<CommandOutput>;
}

/// Output from running a command.
#[derive(Debug, Clone)]
pub struct CommandOutput {
    /// Exit status code.
    pub status: i32,
    /// Standard output.
    pub stdout: String,
    /// Standard error.
    pub stderr: String,
}

impl CommandOutput {
    /// Check if the command succeeded (exit code 0).
    pub fn success(&self) -> bool {
        self.status == 0
    }
}

/// Default implementation of DiskDiscovery using sysinfo.
pub struct SystemDiskDiscovery;

impl DiskDiscovery for SystemDiskDiscovery {
    fn discover_disks(&self) -> Vec<DiskInfo> {
        crate::disk::discover_disks()
    }
    
    fn is_data_disk(&self, disk: &DiskInfo) -> bool {
        let mount_point = disk.mount_point.to_string_lossy();
        
        // Exclude OS disk mount points
        if mount_point == "/" || mount_point.starts_with("/boot") {
            return false;
        }
        if mount_point.to_uppercase().starts_with("C:") {
            return false;
        }
        
        // Exclude removable disks
        !disk.is_removable
    }
}

/// Default implementation of CommandRunner using std::process::Command.
pub struct SystemCommandRunner;

impl CommandRunner for SystemCommandRunner {
    fn command_exists(&self, command: &str) -> bool {
        #[cfg(target_os = "windows")]
        let check = std::process::Command::new("where")
            .arg(command)
            .output();

        #[cfg(not(target_os = "windows"))]
        let check = std::process::Command::new("which")
            .arg(command)
            .output();

        match check {
            Ok(output) => output.status.success(),
            Err(_) => false,
        }
    }
    
    fn run_command(&self, command: &str, args: Vec<String>) -> Result<CommandOutput> {
        let output = std::process::Command::new(command)
            .args(&args)
            .output()
            .map_err(|e| crate::Error::Io(e))?;
        
        Ok(CommandOutput {
            status: output.status.code().unwrap_or(-1),
            stdout: String::from_utf8_lossy(&output.stdout).to_string(),
            stderr: String::from_utf8_lossy(&output.stderr).to_string(),
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::disk::DiskType;
    use std::path::PathBuf;

    fn create_test_disk(mount_point: &str, is_removable: bool) -> DiskInfo {
        DiskInfo {
            name: "test_disk".to_string(),
            mount_point: PathBuf::from(mount_point),
            file_system: "ext4".to_string(),
            disk_type: DiskType::SSD,
            total_space: 1_073_741_824,
            available_space: 536_870_912,
            is_removable,
        }
    }

    #[test]
    fn test_system_disk_discovery_excludes_root() {
        let discovery = SystemDiskDiscovery;
        let disk = create_test_disk("/", false);
        assert!(!discovery.is_data_disk(&disk));
    }

    #[test]
    fn test_system_disk_discovery_excludes_boot() {
        let discovery = SystemDiskDiscovery;
        let disk = create_test_disk("/boot", false);
        assert!(!discovery.is_data_disk(&disk));
    }

    #[test]
    fn test_system_disk_discovery_excludes_removable() {
        let discovery = SystemDiskDiscovery;
        let disk = create_test_disk("/mnt/usb", true);
        assert!(!discovery.is_data_disk(&disk));
    }

    #[test]
    fn test_system_disk_discovery_includes_data_disk() {
        let discovery = SystemDiskDiscovery;
        let disk = create_test_disk("/mnt/data", false);
        assert!(discovery.is_data_disk(&disk));
    }

    #[test]
    fn test_command_output_success() {
        let output = CommandOutput {
            status: 0,
            stdout: "success".to_string(),
            stderr: String::new(),
        };
        assert!(output.success());
    }

    #[test]
    fn test_command_output_failure() {
        let output = CommandOutput {
            status: 1,
            stdout: String::new(),
            stderr: "error".to_string(),
        };
        assert!(!output.success());
    }

    #[test]
    fn test_system_command_runner_command_exists() {
        let runner = SystemCommandRunner;
        // 'cmd' should exist on Windows, 'sh' on Unix
        #[cfg(target_os = "windows")]
        assert!(runner.command_exists("cmd"));
        #[cfg(not(target_os = "windows"))]
        assert!(runner.command_exists("sh"));
    }

    #[test]
    fn test_system_command_runner_command_not_exists() {
        let runner = SystemCommandRunner;
        assert!(!runner.command_exists("this_command_definitely_does_not_exist_12345"));
    }
}
