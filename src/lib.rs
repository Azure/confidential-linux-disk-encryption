//! Confidential Disk Encryption Extension
//!
//! A cross-platform Azure VM extension for confidential disk encryption.
//!
//! This crate provides functionality for:
//! - Discovering and enumerating disks on Linux and Windows
//! - Disk encryption using platform-native tools (LUKS2 on Linux, BitLocker on Windows)
//! - Integration with Azure VM extension infrastructure
//! - Centralized logging with the `tracing` crate
//!
//! # Architecture
//!
//! The extension is installed by Azure and runs as a background handler:
//!
//! ```text
//! Azure Platform
//!     │
//!     ▼
//! Extension Handler (install/enable/disable/update/uninstall)
//!     │
//!     ├── Logging (tracing → file)
//!     │
//!     ├── Disk Discovery
//!     │
//!     └── Encryption Engine
//!             │
//!             ├── LUKS2 (Linux)
//!             └── BitLocker (Windows)
//! ```
//!
//! # Usage
//!
//! The extension is not invoked directly by users. It is managed by Azure
//! and responds to lifecycle events (install, enable, disable, etc.).
//!
//! For development/testing, you can use the handler directly:
//!
//! ```no_run
//! use confidential_disk_encryption::handler::ExtensionHandler;
//! use confidential_disk_encryption::logging;
//!
//! // Initialize logging
//! let _guard = logging::init_dev_logging().expect("Failed to init logging");
//!
//! // Create handler and run enable (main operation)
//! let handler = ExtensionHandler::new_dry_run();
//! handler.handle_enable().expect("Enable failed");
//! ```

pub mod disk;
pub mod error;
pub mod handler;
pub mod logging;

// Re-export commonly used types at the crate root
pub use error::{Error, Result};
pub use handler::ExtensionHandler;
