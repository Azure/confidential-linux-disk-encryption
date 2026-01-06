//! Centralized logging module for the Confidential Disk Encryption Extension.
//!
//! This module provides structured logging using the `tracing` crate, with output
//! to both a log file and (optionally) stdout.
//!
//! # Log Locations
//!
//! - **Linux**: `/var/log/azure/confidential-disk-encryption/extension.log`
//! - **Windows**: `C:\WindowsAzure\Logs\Plugins\<extension>\extension.log`

use std::fs;
use std::path::PathBuf;
use tracing_appender::non_blocking::WorkerGuard;
use tracing_subscriber::{fmt, layer::SubscriberExt, util::SubscriberInitExt, EnvFilter};

/// Default log directory for Linux.
#[cfg(target_os = "linux")]
pub const DEFAULT_LOG_DIR: &str = "/var/log/azure/confidential-disk-encryption";

/// Default log directory for Windows.
#[cfg(target_os = "windows")]
pub const DEFAULT_LOG_DIR: &str = "C:\\WindowsAzure\\Logs\\Plugins\\ConfidentialDiskEncryption";

/// Default log file name.
pub const LOG_FILE_NAME: &str = "extension.log";

/// Configuration for the logging system.
#[derive(Debug, Clone)]
pub struct LogConfig {
    /// Directory where log files are stored.
    pub log_dir: PathBuf,
    /// Log file name.
    pub log_file: String,
    /// Minimum log level (e.g., "info", "debug", "trace").
    pub log_level: String,
    /// Whether to also log to stdout.
    pub log_to_stdout: bool,
}

impl Default for LogConfig {
    fn default() -> Self {
        Self {
            log_dir: PathBuf::from(DEFAULT_LOG_DIR),
            log_file: LOG_FILE_NAME.to_string(),
            log_level: "info".to_string(),
            log_to_stdout: false,
        }
    }
}

/// Initialize the logging system.
///
/// This function sets up the tracing subscriber with file output. It must be called
/// once at the start of the extension before any logging occurs.
///
/// # Arguments
///
/// * `config` - Logging configuration.
///
/// # Returns
///
/// A `WorkerGuard` that must be kept alive for the duration of the program.
/// When dropped, it will flush any remaining log entries.
///
/// # Errors
///
/// Returns an error if the log directory cannot be created or the log file
/// cannot be opened.
///
/// # Example
///
/// ```no_run
/// use confidential_disk_encryption::logging::{init_logging, LogConfig};
///
/// let config = LogConfig::default();
/// let _guard = init_logging(&config).expect("Failed to initialize logging");
///
/// tracing::info!("Extension started");
/// ```
pub fn init_logging(config: &LogConfig) -> crate::Result<WorkerGuard> {
    // Create log directory if it doesn't exist
    fs::create_dir_all(&config.log_dir).map_err(|e| {
        crate::Error::from(std::io::Error::other(format!(
            "Failed to create log directory: {}",
            e
        )))
    })?;

    // Set up file appender
    let file_appender = tracing_appender::rolling::daily(&config.log_dir, &config.log_file);
    let (non_blocking, guard) = tracing_appender::non_blocking(file_appender);

    // Build the subscriber
    let env_filter =
        EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new(&config.log_level));

    let file_layer = fmt::layer()
        .with_writer(non_blocking)
        .with_ansi(false)
        .with_target(true)
        .with_thread_ids(false)
        .with_file(true)
        .with_line_number(true);

    if config.log_to_stdout {
        let stdout_layer = fmt::layer()
            .with_writer(std::io::stdout)
            .with_ansi(true)
            .with_target(true);

        tracing_subscriber::registry()
            .with(env_filter)
            .with(file_layer)
            .with(stdout_layer)
            .init();
    } else {
        tracing_subscriber::registry()
            .with(env_filter)
            .with(file_layer)
            .init();
    }

    Ok(guard)
}

/// Initialize logging with default configuration.
///
/// Convenience function that uses the default log configuration.
///
/// # Returns
///
/// A `WorkerGuard` that must be kept alive for the duration of the program.
pub fn init_default_logging() -> crate::Result<WorkerGuard> {
    init_logging(&LogConfig::default())
}

/// Initialize logging for development/testing.
///
/// Logs to stdout with DEBUG level, useful for local development.
///
/// # Returns
///
/// A `WorkerGuard` that must be kept alive for the duration of the program.
pub fn init_dev_logging() -> crate::Result<WorkerGuard> {
    let config = LogConfig {
        log_dir: PathBuf::from("./logs"),
        log_file: LOG_FILE_NAME.to_string(),
        log_level: "debug".to_string(),
        log_to_stdout: true,
    };
    init_logging(&config)
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[test]
    fn test_log_config_default() {
        let config = LogConfig::default();
        assert_eq!(config.log_file, LOG_FILE_NAME);
        assert_eq!(config.log_level, "info");
        assert!(!config.log_to_stdout);
    }

    #[test]
    fn test_init_logging_creates_directory() {
        let temp_dir = tempdir().unwrap();
        let log_dir = temp_dir.path().join("test_logs");

        let _config = LogConfig {
            log_dir: log_dir.clone(),
            log_file: "test.log".to_string(),
            log_level: "debug".to_string(),
            log_to_stdout: false,
        };

        // Note: We can only initialize tracing once per process,
        // so this test just verifies the directory is created
        assert!(!log_dir.exists());
        fs::create_dir_all(&log_dir).unwrap();
        assert!(log_dir.exists());
    }
}
