//! Error types for the Confidential Disk Encryption Extension.
//!
//! This module provides a unified error type for all operations in the crate.

use thiserror::Error;

/// The main error type for the Confidential Disk Encryption Extension.
#[derive(Error, Debug)]
pub enum Error {
    /// No disks were found on the system.
    #[error("No disks found on this system")]
    NoDisksFound,

    /// A disk operation failed.
    #[error("Disk operation failed: {0}")]
    DiskOperation(String),

    /// An I/O error occurred.
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),

    /// A platform-specific error occurred.
    #[error("Platform error: {0}")]
    Platform(String),

    /// An invalid configuration was provided.
    #[error("Invalid configuration: {0}")]
    InvalidConfiguration(String),
}

/// A specialized Result type for disk encryption operations.
pub type Result<T> = std::result::Result<T, Error>;
