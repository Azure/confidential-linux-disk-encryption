//! Disk discovery and information module.
//!
//! This module provides functionality for discovering and querying disk information
//! on both Linux and Windows platforms.

use std::path::PathBuf;
use sysinfo::Disks;

/// Information about a single disk.
#[derive(Debug, Clone)]
pub struct DiskInfo {
    /// The name of the disk (e.g., "sda", "C:")
    pub name: String,
    /// The mount point of the disk
    pub mount_point: PathBuf,
    /// The filesystem type (e.g., "ext4", "NTFS")
    pub file_system: String,
    /// The disk type (SSD, HDD, etc.)
    pub disk_type: DiskType,
    /// Total space in bytes
    pub total_space: u64,
    /// Available space in bytes
    pub available_space: u64,
    /// Whether the disk is removable
    pub is_removable: bool,
}

impl DiskInfo {
    /// Returns the used space in bytes.
    pub fn used_space(&self) -> u64 {
        self.total_space.saturating_sub(self.available_space)
    }

    /// Returns the usage percentage (0.0 to 100.0).
    pub fn usage_percent(&self) -> f64 {
        if self.total_space > 0 {
            (self.used_space() as f64 / self.total_space as f64) * 100.0
        } else {
            0.0
        }
    }

    /// Returns the total space in gigabytes.
    pub fn total_space_gb(&self) -> f64 {
        self.total_space as f64 / 1_073_741_824.0
    }

    /// Returns the available space in gigabytes.
    pub fn available_space_gb(&self) -> f64 {
        self.available_space as f64 / 1_073_741_824.0
    }

    /// Returns the used space in gigabytes.
    pub fn used_space_gb(&self) -> f64 {
        self.used_space() as f64 / 1_073_741_824.0
    }
}

/// The type of disk.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DiskType {
    /// Solid State Drive
    SSD,
    /// Hard Disk Drive
    HDD,
    /// Unknown disk type
    Unknown,
}

impl std::fmt::Display for DiskType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            DiskType::SSD => write!(f, "SSD"),
            DiskType::HDD => write!(f, "HDD"),
            DiskType::Unknown => write!(f, "Unknown"),
        }
    }
}

/// Discovers all disks on the system.
///
/// # Returns
///
/// A vector of `DiskInfo` structs representing all discovered disks.
///
/// # Example
///
/// ```no_run
/// use confidential_disk_encryption::disk;
///
/// let disks = disk::discover_disks();
/// for disk in &disks {
///     println!("Found disk: {} at {}", disk.name, disk.mount_point.display());
/// }
/// ```
pub fn discover_disks() -> Vec<DiskInfo> {
    let disks = Disks::new_with_refreshed_list();

    disks
        .list()
        .iter()
        .map(|disk| {
            let disk_type = match disk.kind() {
                sysinfo::DiskKind::SSD => DiskType::SSD,
                sysinfo::DiskKind::HDD => DiskType::HDD,
                _ => DiskType::Unknown,
            };

            DiskInfo {
                name: disk.name().to_string_lossy().to_string(),
                mount_point: disk.mount_point().to_path_buf(),
                file_system: disk.file_system().to_string_lossy().to_string(),
                disk_type,
                total_space: disk.total_space(),
                available_space: disk.available_space(),
                is_removable: disk.is_removable(),
            }
        })
        .collect()
}

/// Prints disk information to stdout in a formatted manner.
///
/// # Arguments
///
/// * `disks` - A slice of `DiskInfo` structs to print.
pub fn print_disk_info(disks: &[DiskInfo]) {
    if disks.is_empty() {
        println!("No disks found on this system.");
        return;
    }

    for disk in disks {
        println!("Disk: {}", disk.name);
        println!("  Mount Point:    {}", disk.mount_point.display());
        println!("  File System:    {}", disk.file_system);
        println!("  Type:           {}", disk.disk_type);
        println!("  Total Space:    {:.2} GB", disk.total_space_gb());
        println!("  Available:      {:.2} GB", disk.available_space_gb());
        println!(
            "  Used:           {:.2} GB ({:.1}%)",
            disk.used_space_gb(),
            disk.usage_percent()
        );
        println!("  Removable:      {}", disk.is_removable);
        println!();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn create_test_disk(total: u64, available: u64) -> DiskInfo {
        DiskInfo {
            name: "test".to_string(),
            mount_point: PathBuf::from("/mnt/test"),
            file_system: "ext4".to_string(),
            disk_type: DiskType::SSD,
            total_space: total,
            available_space: available,
            is_removable: false,
        }
    }

    #[test]
    fn test_disk_info_calculations() {
        let disk = create_test_disk(1_073_741_824, 536_870_912); // 1 GB total, 0.5 GB available

        assert_eq!(disk.used_space(), 536_870_912);
        assert!((disk.usage_percent() - 50.0).abs() < 0.01);
        assert!((disk.total_space_gb() - 1.0).abs() < 0.01);
        assert!((disk.available_space_gb() - 0.5).abs() < 0.01);
        assert!((disk.used_space_gb() - 0.5).abs() < 0.01);
    }

    #[test]
    fn test_disk_info_zero_space() {
        let disk = create_test_disk(0, 0);

        assert_eq!(disk.used_space(), 0);
        assert_eq!(disk.usage_percent(), 0.0);
        assert_eq!(disk.total_space_gb(), 0.0);
    }

    #[test]
    fn test_disk_info_full_disk() {
        let disk = create_test_disk(1_073_741_824, 0); // Full disk

        assert_eq!(disk.used_space(), 1_073_741_824);
        assert!((disk.usage_percent() - 100.0).abs() < 0.01);
    }

    #[test]
    fn test_disk_info_empty_disk() {
        let disk = create_test_disk(1_073_741_824, 1_073_741_824); // Empty disk

        assert_eq!(disk.used_space(), 0);
        assert!((disk.usage_percent() - 0.0).abs() < 0.01);
    }

    #[test]
    fn test_disk_info_large_disk() {
        // 1 TB disk
        let disk = create_test_disk(1_099_511_627_776, 549_755_813_888);

        assert!((disk.total_space_gb() - 1024.0).abs() < 0.01);
        assert!((disk.available_space_gb() - 512.0).abs() < 0.01);
    }

    #[test]
    fn test_disk_info_saturating_sub() {
        // Edge case: available > total (shouldn't happen, but test saturating behavior)
        let mut disk = create_test_disk(100, 200);
        disk.available_space = 200; // Manually set to test saturating_sub

        assert_eq!(disk.used_space(), 0); // Should not underflow
    }

    #[test]
    fn test_disk_type_display() {
        assert_eq!(format!("{}", DiskType::SSD), "SSD");
        assert_eq!(format!("{}", DiskType::HDD), "HDD");
        assert_eq!(format!("{}", DiskType::Unknown), "Unknown");
    }

    #[test]
    fn test_disk_type_equality() {
        assert_eq!(DiskType::SSD, DiskType::SSD);
        assert_ne!(DiskType::SSD, DiskType::HDD);
        assert_ne!(DiskType::HDD, DiskType::Unknown);
    }

    #[test]
    fn test_disk_type_copy() {
        let disk_type = DiskType::SSD;
        let copy = disk_type; // Copy
        assert_eq!(disk_type, copy);
    }

    #[test]
    fn test_disk_info_clone() {
        let disk = create_test_disk(1024, 512);
        let cloned = disk.clone();

        assert_eq!(disk.name, cloned.name);
        assert_eq!(disk.total_space, cloned.total_space);
    }

    #[test]
    fn test_disk_info_debug() {
        let disk = create_test_disk(1024, 512);
        let debug = format!("{:?}", disk);

        assert!(debug.contains("DiskInfo"));
        assert!(debug.contains("test"));
    }

    #[test]
    fn test_discover_disks_runs() {
        // This test just verifies that discover_disks() runs without panicking
        let disks = discover_disks();
        // On most systems, there should be at least one disk
        // but we don't assert this as it depends on the environment
        let _ = disks;
    }

    #[test]
    fn test_print_disk_info_empty() {
        // Just verify it doesn't panic with empty list
        print_disk_info(&[]);
    }

    #[test]
    fn test_print_disk_info_single() {
        // Just verify it doesn't panic
        let disk = create_test_disk(1_073_741_824, 536_870_912);
        print_disk_info(&[disk]);
    }
}
