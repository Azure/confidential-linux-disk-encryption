//! Error types for the Confidential Disk Encryption Extension.
//!
//! This module provides structured error types with unique error codes
//! for easy identification, logging, and telemetry.

use std::fmt;
use thiserror::Error;

/// Error codes for the Confidential Disk Encryption Extension.
///
/// Each error has a unique code in the format `CDE###` where:
/// - `CDE` = Confidential Disk Encryption
/// - `###` = Numeric identifier
///
/// Codes are grouped by category:
/// - `CDE001-099`: General/Initialization errors
/// - `CDE100-199`: Disk operation errors
/// - `CDE200-299`: Encryption errors
/// - `CDE300-399`: Key management errors (KeyVault, TPM)
/// - `CDE400-499`: Configuration errors
/// - `CDE500-599`: Platform/System errors
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum ErrorCode {
    // =========================================================================
    // General errors (CDE001-099)
    // =========================================================================
    /// CDE001: Extension initialization failed
    InitializationFailed,
    /// CDE002: Prerequisites not met
    PrerequisitesNotMet,
    /// CDE003: Invalid command or operation
    InvalidOperation,

    // =========================================================================
    // Disk errors (CDE100-199)
    // =========================================================================
    /// CDE100: No disks found on the system
    NoDisksFound,
    /// CDE101: Failed to discover disks
    DiskDiscoveryFailed,
    /// CDE102: Failed to read disk information
    DiskReadFailed,
    /// CDE103: Disk is busy or locked
    DiskBusy,
    /// CDE104: Disk not found
    DiskNotFound,
    /// CDE105: Invalid disk state
    InvalidDiskState,

    // =========================================================================
    // Encryption errors (CDE200-299)
    // =========================================================================
    /// CDE200: Encryption operation failed
    EncryptionFailed,
    /// CDE201: Decryption operation failed
    DecryptionFailed,
    /// CDE202: Disk already encrypted
    AlreadyEncrypted,
    /// CDE203: LUKS format failed
    LuksFormatFailed,
    /// CDE204: BitLocker operation failed
    BitLockerFailed,
    /// CDE205: cryptsetup not available
    CryptsetupNotFound,
    /// CDE206: Auto-unlock setup failed
    AutoUnlockFailed,

    // =========================================================================
    // Key management errors (CDE300-399)
    // =========================================================================
    /// CDE300: Key Vault operation failed
    KeyVaultError,
    /// CDE301: Key Vault authentication failed
    KeyVaultAuthFailed,
    /// CDE302: Key not found in Key Vault
    KeyNotFound,
    /// CDE303: TPM operation failed
    TpmError,
    /// CDE304: TPM not available
    TpmNotAvailable,
    /// CDE305: TPM enrollment failed
    TpmEnrollmentFailed,
    /// CDE306: Key generation failed
    KeyGenerationFailed,

    // =========================================================================
    // Configuration errors (CDE400-499)
    // =========================================================================
    /// CDE400: Invalid configuration
    InvalidConfiguration,
    /// CDE401: Missing required configuration
    MissingConfiguration,
    /// CDE402: Configuration file not found
    ConfigFileNotFound,
    /// CDE403: Configuration parse error
    ConfigParseError,

    // =========================================================================
    // Platform/System errors (CDE500-599)
    // =========================================================================
    /// CDE500: I/O error
    IoError,
    /// CDE501: Permission denied
    PermissionDenied,
    /// CDE502: Command execution failed
    CommandFailed,
    /// CDE503: Platform not supported
    PlatformNotSupported,
    /// CDE504: System resource unavailable
    ResourceUnavailable,
    /// CDE505: Timeout
    Timeout,
}

impl ErrorCode {
    /// Get the numeric code as a string (e.g., "CDE001").
    pub fn code(&self) -> &'static str {
        match self {
            // General
            ErrorCode::InitializationFailed => "CDE001",
            ErrorCode::PrerequisitesNotMet => "CDE002",
            ErrorCode::InvalidOperation => "CDE003",
            // Disk
            ErrorCode::NoDisksFound => "CDE100",
            ErrorCode::DiskDiscoveryFailed => "CDE101",
            ErrorCode::DiskReadFailed => "CDE102",
            ErrorCode::DiskBusy => "CDE103",
            ErrorCode::DiskNotFound => "CDE104",
            ErrorCode::InvalidDiskState => "CDE105",
            // Encryption
            ErrorCode::EncryptionFailed => "CDE200",
            ErrorCode::DecryptionFailed => "CDE201",
            ErrorCode::AlreadyEncrypted => "CDE202",
            ErrorCode::LuksFormatFailed => "CDE203",
            ErrorCode::BitLockerFailed => "CDE204",
            ErrorCode::CryptsetupNotFound => "CDE205",
            ErrorCode::AutoUnlockFailed => "CDE206",
            // Key management
            ErrorCode::KeyVaultError => "CDE300",
            ErrorCode::KeyVaultAuthFailed => "CDE301",
            ErrorCode::KeyNotFound => "CDE302",
            ErrorCode::TpmError => "CDE303",
            ErrorCode::TpmNotAvailable => "CDE304",
            ErrorCode::TpmEnrollmentFailed => "CDE305",
            ErrorCode::KeyGenerationFailed => "CDE306",
            // Configuration
            ErrorCode::InvalidConfiguration => "CDE400",
            ErrorCode::MissingConfiguration => "CDE401",
            ErrorCode::ConfigFileNotFound => "CDE402",
            ErrorCode::ConfigParseError => "CDE403",
            // Platform
            ErrorCode::IoError => "CDE500",
            ErrorCode::PermissionDenied => "CDE501",
            ErrorCode::CommandFailed => "CDE502",
            ErrorCode::PlatformNotSupported => "CDE503",
            ErrorCode::ResourceUnavailable => "CDE504",
            ErrorCode::Timeout => "CDE505",
        }
    }

    /// Get the default human-readable message for this error code.
    pub fn default_message(&self) -> &'static str {
        match self {
            // General
            ErrorCode::InitializationFailed => "Extension initialization failed",
            ErrorCode::PrerequisitesNotMet => "VM does not meet prerequisites for disk encryption",
            ErrorCode::InvalidOperation => "Invalid command or operation",
            // Disk
            ErrorCode::NoDisksFound => "No data disks found on this system",
            ErrorCode::DiskDiscoveryFailed => "Failed to discover attached disks",
            ErrorCode::DiskReadFailed => "Failed to read disk information",
            ErrorCode::DiskBusy => "Disk is busy or locked by another process",
            ErrorCode::DiskNotFound => "Specified disk was not found",
            ErrorCode::InvalidDiskState => "Disk is in an invalid state for this operation",
            // Encryption
            ErrorCode::EncryptionFailed => "Disk encryption operation failed",
            ErrorCode::DecryptionFailed => "Disk decryption operation failed",
            ErrorCode::AlreadyEncrypted => "Disk is already encrypted",
            ErrorCode::LuksFormatFailed => "Failed to format disk with LUKS2",
            ErrorCode::BitLockerFailed => "BitLocker operation failed",
            ErrorCode::CryptsetupNotFound => "cryptsetup utility not found",
            ErrorCode::AutoUnlockFailed => "Failed to configure automatic disk unlock",
            // Key management
            ErrorCode::KeyVaultError => "Azure Key Vault operation failed",
            ErrorCode::KeyVaultAuthFailed => "Failed to authenticate to Azure Key Vault",
            ErrorCode::KeyNotFound => "Encryption key not found in Key Vault",
            ErrorCode::TpmError => "TPM operation failed",
            ErrorCode::TpmNotAvailable => "TPM device not available on this VM",
            ErrorCode::TpmEnrollmentFailed => "Failed to enroll disk with TPM",
            ErrorCode::KeyGenerationFailed => "Failed to generate encryption key",
            // Configuration
            ErrorCode::InvalidConfiguration => "Invalid configuration provided",
            ErrorCode::MissingConfiguration => "Required configuration is missing",
            ErrorCode::ConfigFileNotFound => "Configuration file not found",
            ErrorCode::ConfigParseError => "Failed to parse configuration file",
            // Platform
            ErrorCode::IoError => "I/O operation failed",
            ErrorCode::PermissionDenied => "Permission denied",
            ErrorCode::CommandFailed => "Command execution failed",
            ErrorCode::PlatformNotSupported => "This platform is not supported",
            ErrorCode::ResourceUnavailable => "Required system resource is unavailable",
            ErrorCode::Timeout => "Operation timed out",
        }
    }

    /// Get a hint for resolving this error.
    pub fn hint(&self) -> Option<&'static str> {
        match self {
            ErrorCode::PrerequisitesNotMet => Some("Run 'check-prereqs' command for details"),
            ErrorCode::NoDisksFound => {
                Some("Attach data disks to the VM before enabling encryption")
            }
            ErrorCode::CryptsetupNotFound => Some("Install cryptsetup: apt install cryptsetup"),
            ErrorCode::PermissionDenied => Some("Run the extension as root/Administrator"),
            ErrorCode::TpmNotAvailable => Some("Ensure VM is Trusted Launch or Confidential VM"),
            ErrorCode::KeyVaultAuthFailed => Some("Check managed identity has Key Vault access"),
            _ => None,
        }
    }
}

impl fmt::Display for ErrorCode {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.code())
    }
}

/// The main error type for the Confidential Disk Encryption Extension.
#[derive(Error, Debug)]
#[error("[{code}] {message}")]
pub struct Error {
    /// Unique error code.
    pub code: ErrorCode,
    /// Human-readable error message.
    pub message: String,
    /// Additional details about the error.
    pub details: Option<String>,
    /// Underlying error that caused this error.
    #[source]
    pub source: Option<Box<dyn std::error::Error + Send + Sync>>,
}

impl Error {
    /// Create a new error with the default message for the given code.
    pub fn new(code: ErrorCode) -> Self {
        Self {
            code,
            message: code.default_message().to_string(),
            details: None,
            source: None,
        }
    }

    /// Create a new error with a custom message.
    pub fn with_message(code: ErrorCode, message: impl Into<String>) -> Self {
        Self {
            code,
            message: message.into(),
            details: None,
            source: None,
        }
    }

    /// Add details to the error.
    pub fn with_details(mut self, details: impl Into<String>) -> Self {
        self.details = Some(details.into());
        self
    }

    /// Add a source error.
    pub fn with_source(mut self, source: impl std::error::Error + Send + Sync + 'static) -> Self {
        self.source = Some(Box::new(source));
        self
    }

    /// Get the error code string (e.g., "CDE001").
    pub fn code_str(&self) -> &'static str {
        self.code.code()
    }

    /// Get a hint for resolving this error, if available.
    pub fn hint(&self) -> Option<&'static str> {
        self.code.hint()
    }

    /// Format the error for display to users (includes hint if available).
    pub fn user_message(&self) -> String {
        let mut msg = format!("[{}] {}", self.code.code(), self.message);
        if let Some(details) = &self.details {
            msg.push_str(&format!("\nDetails: {}", details));
        }
        if let Some(hint) = self.hint() {
            msg.push_str(&format!("\nHint: {}", hint));
        }
        msg
    }
}

// Convenient conversion from std::io::Error
impl From<std::io::Error> for Error {
    fn from(err: std::io::Error) -> Self {
        Error::with_message(ErrorCode::IoError, err.to_string()).with_source(err)
    }
}

/// A specialized Result type for disk encryption operations.
pub type Result<T> = std::result::Result<T, Error>;

// ============================================================================
// Legacy compatibility - these will be removed in a future version
// ============================================================================

/// Legacy error constructors for backward compatibility.
impl Error {
    /// Create a NoDisksFound error (legacy).
    #[deprecated(note = "Use Error::new(ErrorCode::NoDisksFound) instead")]
    pub fn no_disks_found() -> Self {
        Self::new(ErrorCode::NoDisksFound)
    }

    /// Create a DiskOperation error (legacy).
    #[deprecated(note = "Use Error::with_message(ErrorCode::*, msg) instead")]
    pub fn disk_operation(msg: impl Into<String>) -> Self {
        Self::with_message(ErrorCode::EncryptionFailed, msg)
    }

    /// Create a Platform error (legacy).
    #[deprecated(note = "Use Error::with_message(ErrorCode::*, msg) instead")]
    pub fn platform(msg: impl Into<String>) -> Self {
        Self::with_message(ErrorCode::PlatformNotSupported, msg)
    }

    /// Create an InvalidConfiguration error (legacy).
    #[deprecated(note = "Use Error::with_message(ErrorCode::InvalidConfiguration, msg) instead")]
    pub fn invalid_configuration(msg: impl Into<String>) -> Self {
        Self::with_message(ErrorCode::InvalidConfiguration, msg)
    }

    /// Create a Prerequisites error (legacy).
    #[deprecated(note = "Use Error::with_message(ErrorCode::PrerequisitesNotMet, msg) instead")]
    pub fn prerequisites(msg: impl Into<String>) -> Self {
        Self::with_message(ErrorCode::PrerequisitesNotMet, msg)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // =========================================================================
    // ErrorCode tests
    // =========================================================================

    #[test]
    fn test_error_code_string() {
        assert_eq!(ErrorCode::NoDisksFound.code(), "CDE100");
        assert_eq!(ErrorCode::PrerequisitesNotMet.code(), "CDE002");
        assert_eq!(ErrorCode::IoError.code(), "CDE500");
    }

    #[test]
    fn test_error_code_all_categories() {
        // General
        assert!(ErrorCode::InitializationFailed.code().starts_with("CDE0"));
        assert!(ErrorCode::PrerequisitesNotMet.code().starts_with("CDE0"));
        assert!(ErrorCode::InvalidOperation.code().starts_with("CDE0"));

        // Disk
        assert!(ErrorCode::NoDisksFound.code().starts_with("CDE1"));
        assert!(ErrorCode::DiskBusy.code().starts_with("CDE1"));

        // Encryption
        assert!(ErrorCode::EncryptionFailed.code().starts_with("CDE2"));
        assert!(ErrorCode::CryptsetupNotFound.code().starts_with("CDE2"));

        // Key management
        assert!(ErrorCode::TpmNotAvailable.code().starts_with("CDE3"));
        assert!(ErrorCode::KeyGenerationFailed.code().starts_with("CDE3"));

        // Configuration
        assert!(ErrorCode::InvalidConfiguration.code().starts_with("CDE4"));

        // Platform
        assert!(ErrorCode::IoError.code().starts_with("CDE5"));
        assert!(ErrorCode::PermissionDenied.code().starts_with("CDE5"));
    }

    #[test]
    fn test_error_code_display() {
        let code = ErrorCode::NoDisksFound;
        assert_eq!(format!("{}", code), "CDE100");
    }

    #[test]
    fn test_error_code_default_messages_not_empty() {
        let codes = [
            ErrorCode::InitializationFailed,
            ErrorCode::NoDisksFound,
            ErrorCode::EncryptionFailed,
            ErrorCode::TpmNotAvailable,
            ErrorCode::InvalidConfiguration,
            ErrorCode::IoError,
        ];

        for code in codes {
            assert!(
                !code.default_message().is_empty(),
                "Code {:?} has empty message",
                code
            );
        }
    }

    #[test]
    fn test_error_code_hints() {
        // Codes with hints
        assert!(ErrorCode::PrerequisitesNotMet.hint().is_some());
        assert!(ErrorCode::NoDisksFound.hint().is_some());
        assert!(ErrorCode::CryptsetupNotFound.hint().is_some());
        assert!(ErrorCode::PermissionDenied.hint().is_some());
        assert!(ErrorCode::TpmNotAvailable.hint().is_some());

        // Codes without hints
        assert!(ErrorCode::InitializationFailed.hint().is_none());
        assert!(ErrorCode::IoError.hint().is_none());
    }

    #[test]
    fn test_error_code_equality() {
        assert_eq!(ErrorCode::NoDisksFound, ErrorCode::NoDisksFound);
        assert_ne!(ErrorCode::NoDisksFound, ErrorCode::DiskBusy);
    }

    #[test]
    fn test_error_code_hash() {
        use std::collections::HashSet;
        let mut set = HashSet::new();
        set.insert(ErrorCode::NoDisksFound);
        set.insert(ErrorCode::DiskBusy);
        set.insert(ErrorCode::NoDisksFound); // Duplicate

        assert_eq!(set.len(), 2);
    }

    #[test]
    fn test_error_code_copy() {
        let code = ErrorCode::NoDisksFound;
        let copy = code; // Copy
        assert_eq!(code, copy);
    }

    // =========================================================================
    // Error tests
    // =========================================================================

    #[test]
    fn test_error_default_message() {
        let err = Error::new(ErrorCode::NoDisksFound);
        assert_eq!(err.code, ErrorCode::NoDisksFound);
        assert!(err.message.contains("No data disks"));
    }

    #[test]
    fn test_error_custom_message() {
        let err = Error::with_message(ErrorCode::DiskBusy, "Disk /dev/sdb is in use");
        assert_eq!(err.code, ErrorCode::DiskBusy);
        assert_eq!(err.message, "Disk /dev/sdb is in use");
    }

    #[test]
    fn test_error_with_details() {
        let err = Error::new(ErrorCode::EncryptionFailed).with_details("Failed at step 3 of 5");
        assert!(err.details.is_some());
        assert_eq!(err.details.unwrap(), "Failed at step 3 of 5");
    }

    #[test]
    fn test_error_with_source() {
        let io_err = std::io::Error::new(std::io::ErrorKind::NotFound, "file not found");
        let err = Error::new(ErrorCode::IoError).with_source(io_err);

        assert!(err.source.is_some());
    }

    #[test]
    fn test_error_builder_chain() {
        let io_err = std::io::Error::other("test");
        let err = Error::with_message(ErrorCode::EncryptionFailed, "Custom message")
            .with_details("Additional details")
            .with_source(io_err);

        assert_eq!(err.message, "Custom message");
        assert!(err.details.is_some());
        assert!(err.source.is_some());
    }

    #[test]
    fn test_error_display() {
        let err = Error::new(ErrorCode::NoDisksFound);
        let display = format!("{}", err);
        assert!(display.contains("CDE100"));
        assert!(display.contains("No data disks"));
    }

    #[test]
    fn test_error_debug() {
        let err = Error::new(ErrorCode::NoDisksFound);
        let debug = format!("{:?}", err);
        assert!(debug.contains("Error"));
        assert!(debug.contains("NoDisksFound"));
    }

    #[test]
    fn test_error_code_str() {
        let err = Error::new(ErrorCode::NoDisksFound);
        assert_eq!(err.code_str(), "CDE100");
    }

    #[test]
    fn test_error_user_message_with_hint() {
        let err = Error::new(ErrorCode::PermissionDenied);
        let msg = err.user_message();
        assert!(msg.contains("CDE501"));
        assert!(msg.contains("Hint:"));
        assert!(msg.contains("root"));
    }

    #[test]
    fn test_error_user_message_with_details() {
        let err = Error::new(ErrorCode::IoError).with_details("Could not open file");
        let msg = err.user_message();

        assert!(msg.contains("CDE500"));
        assert!(msg.contains("Details:"));
        assert!(msg.contains("Could not open file"));
    }

    #[test]
    fn test_error_user_message_without_hint() {
        let err = Error::new(ErrorCode::IoError);
        let msg = err.user_message();

        assert!(msg.contains("CDE500"));
        assert!(!msg.contains("Hint:"));
    }

    #[test]
    fn test_error_from_io() {
        let io_err = std::io::Error::new(std::io::ErrorKind::NotFound, "file not found");
        let err: Error = io_err.into();
        assert_eq!(err.code, ErrorCode::IoError);
        assert!(err.source.is_some());
        assert!(err.message.contains("file not found"));
    }

    #[test]
    fn test_error_from_io_various_kinds() {
        let kinds = [
            std::io::ErrorKind::NotFound,
            std::io::ErrorKind::PermissionDenied,
            std::io::ErrorKind::ConnectionRefused,
            std::io::ErrorKind::TimedOut,
        ];

        for kind in kinds {
            let io_err = std::io::Error::new(kind, "test");
            let err: Error = io_err.into();
            assert_eq!(err.code, ErrorCode::IoError);
        }
    }

    // =========================================================================
    // Legacy compatibility tests
    // =========================================================================

    #[test]
    #[allow(deprecated)]
    fn test_legacy_no_disks_found() {
        let err = Error::no_disks_found();
        assert_eq!(err.code, ErrorCode::NoDisksFound);
    }

    #[test]
    #[allow(deprecated)]
    fn test_legacy_disk_operation() {
        let err = Error::disk_operation("Test error");
        assert_eq!(err.code, ErrorCode::EncryptionFailed);
    }

    #[test]
    #[allow(deprecated)]
    fn test_legacy_platform() {
        let err = Error::platform("Not supported");
        assert_eq!(err.code, ErrorCode::PlatformNotSupported);
    }

    #[test]
    #[allow(deprecated)]
    fn test_legacy_invalid_configuration() {
        let err = Error::invalid_configuration("Bad config");
        assert_eq!(err.code, ErrorCode::InvalidConfiguration);
    }

    #[test]
    #[allow(deprecated)]
    fn test_legacy_prerequisites() {
        let err = Error::prerequisites("Missing tools");
        assert_eq!(err.code, ErrorCode::PrerequisitesNotMet);
    }
}
