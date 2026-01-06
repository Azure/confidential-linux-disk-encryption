# Error Codes

All errors use the format `CDE###` (Confidential Disk Encryption).

## General (CDE001-099)

| Code | Name | Message |
|------|------|---------|
| CDE001 | InitializationFailed | Extension initialization failed |
| CDE002 | PrerequisitesNotMet | VM does not meet prerequisites for disk encryption |
| CDE003 | InvalidOperation | Invalid command or operation |

## Disk Operations (CDE100-199)

| Code | Name | Message |
|------|------|---------|
| CDE100 | NoDisksFound | No data disks found on this system |
| CDE101 | DiskDiscoveryFailed | Failed to discover attached disks |
| CDE102 | DiskReadFailed | Failed to read disk information |
| CDE103 | DiskBusy | Disk is busy or locked by another process |
| CDE104 | DiskNotFound | Specified disk was not found |
| CDE105 | InvalidDiskState | Disk is in an invalid state for this operation |

## Encryption (CDE200-299)

| Code | Name | Message |
|------|------|---------|
| CDE200 | EncryptionFailed | Disk encryption operation failed |
| CDE201 | DecryptionFailed | Disk decryption operation failed |
| CDE202 | AlreadyEncrypted | Disk is already encrypted |
| CDE203 | LuksFormatFailed | Failed to format disk with LUKS2 |
| CDE204 | BitLockerFailed | BitLocker operation failed |
| CDE205 | CryptsetupNotFound | cryptsetup utility not found |
| CDE206 | AutoUnlockFailed | Failed to configure automatic disk unlock |

## TPM Operations (CDE300-399)

| Code | Name | Message |
|------|------|---------|
| CDE303 | TpmError | TPM operation failed |
| CDE304 | TpmNotAvailable | TPM device not available on this VM |
| CDE305 | TpmEnrollmentFailed | Failed to enroll disk with TPM |
| CDE306 | KeyGenerationFailed | Failed to generate encryption key |

> **Note**: CDE300-302 are reserved.

## Configuration (CDE400-499)

| Code | Name | Message |
|------|------|---------|
| CDE400 | InvalidConfiguration | Invalid configuration provided |
| CDE401 | MissingConfiguration | Required configuration is missing |
| CDE402 | ConfigFileNotFound | Configuration file not found |
| CDE403 | ConfigParseError | Failed to parse configuration file |

## Platform/System (CDE500-599)

| Code | Name | Message |
|------|------|---------|
| CDE500 | IoError | I/O operation failed |
| CDE501 | PermissionDenied | Permission denied |
| CDE502 | CommandFailed | Command execution failed |
| CDE503 | PlatformNotSupported | This platform is not supported |
| CDE504 | ResourceUnavailable | Required system resource is unavailable |
| CDE505 | Timeout | Operation timed out |

## Using Error Codes

```rust
use confidential_disk_encryption::{Error, ErrorCode};

// Create error with default message
let err = Error::new(ErrorCode::NoDisksFound);

// Create error with custom message
let err = Error::with_message(ErrorCode::DiskBusy, "/dev/sdb is in use");

// Add details
let err = Error::new(ErrorCode::EncryptionFailed)
    .with_details("Failed at step 3");

// Error display: "[CDE100] No data disks found on this system"
