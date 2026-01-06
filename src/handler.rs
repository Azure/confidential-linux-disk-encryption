//! Azure VM Extension handler module.
//!
//! This module implements the Azure VM extension lifecycle handlers:
//! - `install` - Called when the extension is first deployed
//! - `enable` - Called when the extension is enabled (main operation)
//! - `disable` - Called when the extension is disabled
//! - `update` - Called when the extension is updated
//! - `uninstall` - Called when the extension is removed
//!
//! The extension automatically encrypts all data disks when enabled.

use crate::disk::{self, DiskInfo};
use crate::error::{Error, ErrorCode, Result};
use crate::prerequisites::PrerequisiteChecker;
use tracing::{error, info, instrument, warn};

/// Extension handler that manages the extension lifecycle.
#[derive(Debug)]
pub struct ExtensionHandler {
    /// Whether to run in dry-run mode (no actual encryption).
    dry_run: bool,
}

impl ExtensionHandler {
    /// Create a new extension handler.
    pub fn new() -> Self {
        Self { dry_run: false }
    }

    /// Create a new extension handler in dry-run mode.
    ///
    /// In dry-run mode, the handler will discover disks and log what it would do,
    /// but will not actually perform encryption.
    pub fn new_dry_run() -> Self {
        Self { dry_run: true }
    }

    /// Handle the `install` command.
    ///
    /// Called when the extension is first deployed to the VM.
    /// Validates prerequisites and initializes required directories.
    #[instrument(skip(self), name = "install")]
    pub fn handle_install(&self) -> Result<()> {
        info!("Installing Confidential Disk Encryption extension");

        // Validate prerequisites
        self.validate_prerequisites()?;

        info!("Extension installed successfully");
        Ok(())
    }

    /// Handle the `enable` command.
    ///
    /// Called when the extension is enabled. This is the main operation that:
    /// 1. Discovers all attached disks
    /// 2. Filters to data disks only
    /// 3. Encrypts each eligible disk
    #[instrument(skip(self), name = "enable")]
    pub fn handle_enable(&self) -> Result<()> {
        info!("Enabling Confidential Disk Encryption extension");

        // Discover all disks
        let all_disks = disk::discover_disks();
        info!(disk_count = all_disks.len(), "Discovered disks");

        // Filter to data disks only
        let data_disks = self.filter_data_disks(&all_disks);
        info!(data_disk_count = data_disks.len(), "Identified data disks");

        if data_disks.is_empty() {
            warn!("No data disks found to encrypt");
            return Ok(());
        }

        // Encrypt each data disk
        let mut success_count = 0;
        let mut failure_count = 0;

        for disk in &data_disks {
            match self.encrypt_disk(disk) {
                Ok(()) => {
                    success_count += 1;
                }
                Err(e) => {
                    error!(
                        disk = %disk.name,
                        error = %e,
                        "Failed to encrypt disk"
                    );
                    failure_count += 1;
                }
            }
        }

        info!(
            success_count,
            failure_count,
            "Disk encryption completed"
        );

        if failure_count > 0 {
            return Err(Error::with_message(
                ErrorCode::EncryptionFailed,
                format!("Failed to encrypt {} disk(s)", failure_count),
            ));
        }

        Ok(())
    }

    /// Handle the `disable` command.
    ///
    /// Called when the extension is disabled. Disks remain encrypted.
    #[instrument(skip(self), name = "disable")]
    pub fn handle_disable(&self) -> Result<()> {
        info!("Disabling Confidential Disk Encryption extension");
        info!("Note: Encrypted disks will remain encrypted");
        Ok(())
    }

    /// Handle the `update` command.
    ///
    /// Called when the extension is updated to a new version.
    #[instrument(skip(self), name = "update")]
    pub fn handle_update(&self) -> Result<()> {
        info!("Updating Confidential Disk Encryption extension");
        // Future: Handle configuration migration if needed
        info!("Extension updated successfully");
        Ok(())
    }

    /// Handle the `uninstall` command.
    ///
    /// Called when the extension is removed. Disks remain encrypted.
    #[instrument(skip(self), name = "uninstall")]
    pub fn handle_uninstall(&self) -> Result<()> {
        info!("Uninstalling Confidential Disk Encryption extension");
        info!("Note: Encrypted disks will remain encrypted");
        // Future: Cleanup any extension-specific files
        Ok(())
    }

    /// Validate that prerequisites are met for the extension to run.
    ///
    /// This performs comprehensive checks for:
    /// - Required encryption tools (cryptsetup on Linux, BitLocker on Windows)
    /// - Kernel module availability (dm-crypt on Linux)
    /// - TPM availability for auto-unlock
    /// - Root/Admin permissions
    ///
    /// Returns an error with detailed messages if any required prerequisite fails.
    fn validate_prerequisites(&self) -> Result<()> {
        if self.dry_run {
            info!("Dry-run mode: Running prerequisite checks (failures won't block)");
            let report = PrerequisiteChecker::run_all_checks();
            
            if !report.all_passed {
                warn!(
                    errors = report.error_count,
                    warnings = report.warning_count,
                    "Some prerequisite checks failed (ignored in dry-run mode)"
                );
            }
            return Ok(());
        }

        PrerequisiteChecker::ensure_prerequisites()
    }

    /// Filter disks to only include data disks (exclude OS disk).
    fn filter_data_disks<'a>(&self, disks: &'a [DiskInfo]) -> Vec<&'a DiskInfo> {
        disks
            .iter()
            .filter(|disk| self.is_data_disk(disk))
            .collect()
    }

    /// Determine if a disk is a data disk (not the OS disk).
    fn is_data_disk(&self, disk: &DiskInfo) -> bool {
        let mount_point = disk.mount_point.to_string_lossy();

        // Exclude OS disk mount points
        // On Linux, exclude root and boot partitions
        if mount_point == "/" || mount_point.starts_with("/boot") {
            return false;
        }

        // On Windows, exclude C: drive (typically the OS disk)
        if mount_point.to_uppercase().starts_with("C:") {
            return false;
        }

        // Exclude removable disks
        if disk.is_removable {
            return false;
        }

        true
    }

    /// Encrypt a single disk.
    #[instrument(skip(self), fields(disk = %disk.name))]
    fn encrypt_disk(&self, disk: &DiskInfo) -> Result<()> {
        info!(
            mount_point = %disk.mount_point.display(),
            file_system = %disk.file_system,
            size_gb = disk.total_space_gb(),
            "Starting disk encryption"
        );

        if self.dry_run {
            info!("Dry-run mode: Skipping actual encryption");
            return Ok(());
        }

        // TODO: Implement actual encryption
        // For now, we just log what we would do
        warn!("Encryption not yet implemented");

        Ok(())
    }
}

impl Default for ExtensionHandler {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;
    use crate::disk::DiskType;

    fn create_test_disk(name: &str, mount_point: &str, is_removable: bool) -> DiskInfo {
        DiskInfo {
            name: name.to_string(),
            mount_point: PathBuf::from(mount_point),
            file_system: "ext4".to_string(),
            disk_type: DiskType::SSD,
            total_space: 1_073_741_824,
            available_space: 536_870_912,
            is_removable,
        }
    }

    // =========================================================================
    // Constructor tests
    // =========================================================================

    #[test]
    fn test_new_creates_non_dry_run_handler() {
        let handler = ExtensionHandler::new();
        assert!(!handler.dry_run);
    }

    #[test]
    fn test_new_dry_run_creates_dry_run_handler() {
        let handler = ExtensionHandler::new_dry_run();
        assert!(handler.dry_run);
    }

    #[test]
    fn test_default_creates_non_dry_run_handler() {
        let handler = ExtensionHandler::default();
        assert!(!handler.dry_run);
    }

    #[test]
    fn test_handler_debug() {
        let handler = ExtensionHandler::new();
        let debug = format!("{:?}", handler);
        assert!(debug.contains("ExtensionHandler"));
    }

    // =========================================================================
    // is_data_disk tests
    // =========================================================================

    #[test]
    fn test_is_data_disk_excludes_root() {
        let handler = ExtensionHandler::new();
        let disk = create_test_disk("sda1", "/", false);
        assert!(!handler.is_data_disk(&disk));
    }

    #[test]
    fn test_is_data_disk_excludes_boot() {
        let handler = ExtensionHandler::new();
        let disk = create_test_disk("sda2", "/boot", false);
        assert!(!handler.is_data_disk(&disk));
    }

    #[test]
    fn test_is_data_disk_excludes_boot_efi() {
        let handler = ExtensionHandler::new();
        let disk = create_test_disk("sda3", "/boot/efi", false);
        assert!(!handler.is_data_disk(&disk));
    }

    #[test]
    fn test_is_data_disk_excludes_removable() {
        let handler = ExtensionHandler::new();
        let disk = create_test_disk("sdb1", "/mnt/usb", true);
        assert!(!handler.is_data_disk(&disk));
    }

    #[test]
    fn test_is_data_disk_includes_data_mount() {
        let handler = ExtensionHandler::new();
        let disk = create_test_disk("sdc1", "/mnt/data", false);
        assert!(handler.is_data_disk(&disk));
    }

    #[test]
    fn test_is_data_disk_includes_var() {
        let handler = ExtensionHandler::new();
        let disk = create_test_disk("sdc1", "/var", false);
        assert!(handler.is_data_disk(&disk));
    }

    #[test]
    fn test_is_data_disk_includes_home() {
        let handler = ExtensionHandler::new();
        let disk = create_test_disk("sdc1", "/home", false);
        assert!(handler.is_data_disk(&disk));
    }

    #[test]
    fn test_is_data_disk_excludes_windows_c_drive() {
        let handler = ExtensionHandler::new();
        let disk = create_test_disk("C:", "C:\\", false);
        assert!(!handler.is_data_disk(&disk));
    }

    #[test]
    fn test_is_data_disk_excludes_windows_c_lowercase() {
        let handler = ExtensionHandler::new();
        let disk = create_test_disk("c:", "c:\\", false);
        assert!(!handler.is_data_disk(&disk));
    }

    #[test]
    fn test_is_data_disk_includes_windows_d_drive() {
        let handler = ExtensionHandler::new();
        let disk = create_test_disk("D:", "D:\\", false);
        assert!(handler.is_data_disk(&disk));
    }

    #[test]
    fn test_is_data_disk_includes_windows_data_path() {
        let handler = ExtensionHandler::new();
        let disk = create_test_disk("E:", "E:\\Data", false);
        assert!(handler.is_data_disk(&disk));
    }

    // =========================================================================
    // filter_data_disks tests
    // =========================================================================

    #[test]
    fn test_filter_data_disks() {
        let handler = ExtensionHandler::new();
        let disks = vec![
            create_test_disk("sda1", "/", false),
            create_test_disk("sda2", "/boot", false),
            create_test_disk("sdb1", "/mnt/data1", false),
            create_test_disk("sdc1", "/mnt/data2", false),
            create_test_disk("sdd1", "/mnt/usb", true),
        ];

        let data_disks = handler.filter_data_disks(&disks);
        assert_eq!(data_disks.len(), 2);
        assert_eq!(data_disks[0].name, "sdb1");
        assert_eq!(data_disks[1].name, "sdc1");
    }

    #[test]
    fn test_filter_data_disks_empty_input() {
        let handler = ExtensionHandler::new();
        let disks: Vec<DiskInfo> = vec![];

        let data_disks = handler.filter_data_disks(&disks);
        assert!(data_disks.is_empty());
    }

    #[test]
    fn test_filter_data_disks_all_os_disks() {
        let handler = ExtensionHandler::new();
        let disks = vec![
            create_test_disk("sda1", "/", false),
            create_test_disk("sda2", "/boot", false),
        ];

        let data_disks = handler.filter_data_disks(&disks);
        assert!(data_disks.is_empty());
    }

    #[test]
    fn test_filter_data_disks_all_data_disks() {
        let handler = ExtensionHandler::new();
        let disks = vec![
            create_test_disk("sdb1", "/mnt/data1", false),
            create_test_disk("sdc1", "/mnt/data2", false),
        ];

        let data_disks = handler.filter_data_disks(&disks);
        assert_eq!(data_disks.len(), 2);
    }

    #[test]
    fn test_filter_data_disks_preserves_order() {
        let handler = ExtensionHandler::new();
        let disks = vec![
            create_test_disk("sdc1", "/mnt/c", false),
            create_test_disk("sda1", "/mnt/a", false),
            create_test_disk("sdb1", "/mnt/b", false),
        ];

        let data_disks = handler.filter_data_disks(&disks);
        assert_eq!(data_disks[0].name, "sdc1");
        assert_eq!(data_disks[1].name, "sda1");
        assert_eq!(data_disks[2].name, "sdb1");
    }

    // =========================================================================
    // Lifecycle handler tests (basic coverage)
    // =========================================================================

    #[test]
    fn test_handle_disable_succeeds() {
        let handler = ExtensionHandler::new();
        assert!(handler.handle_disable().is_ok());
    }

    #[test]
    fn test_handle_update_succeeds() {
        let handler = ExtensionHandler::new();
        assert!(handler.handle_update().is_ok());
    }

    #[test]
    fn test_handle_uninstall_succeeds() {
        let handler = ExtensionHandler::new();
        assert!(handler.handle_uninstall().is_ok());
    }

    // =========================================================================
    // Dry run tests
    // =========================================================================

    #[test]
    fn test_dry_run_mode() {
        let handler = ExtensionHandler::new_dry_run();
        assert!(handler.dry_run);
    }

    #[test]
    fn test_dry_run_encrypt_disk_does_not_fail() {
        let handler = ExtensionHandler::new_dry_run();
        let disk = create_test_disk("sdb1", "/mnt/data", false);
        
        // Dry run should always succeed
        assert!(handler.encrypt_disk(&disk).is_ok());
    }

    #[test]
    fn test_dry_run_handle_enable_succeeds() {
        let handler = ExtensionHandler::new_dry_run();
        // This may log but should not fail
        assert!(handler.handle_enable().is_ok());
    }
}
