//! Confidential Disk Encryption Extension
//!
//! A cross-platform Azure VM extension for confidential disk encryption.
//!
//! This crate provides functionality for:
//! - Discovering and enumerating disks on Linux and Windows
//! - Disk encryption using platform-native tools (LUKS on Linux, BitLocker on Windows)
//! - Integration with Azure VM extension infrastructure
//!
//! # Example
//!
//! ```no_run
//! use confidential_disk_encryption::disk;
//!
//! // Discover all disks on the system
//! let disks = disk::discover_disks();
//!
//! // Print disk information
//! disk::print_disk_info(&disks);
//! ```

pub mod disk;
pub mod error;

// Re-export commonly used types at the crate root
pub use error::{Error, Result};
