# Architecture and Design Patterns for Confidential Disk Encryption Extension

This document describes the architectural patterns and design principles used in this project to help maintain consistency and quality.

## System Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                      Azure Platform                          │
│  (VM Agent invokes extension with install/enable/disable)   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               Extension Entry Point (main.rs)                │
│  - Parse command-line arguments                              │
│  - Initialize logging                                        │
│  - Route to appropriate handler                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│            Extension Handler (handler.rs)                    │
│  - handle_install() → Validate prerequisites                │
│  - handle_enable()  → Encrypt all data disks                │
│  - handle_disable() → No-op (disks stay encrypted)          │
│  - handle_update()  → Migrate if needed                     │
│  - handle_uninstall() → No-op (disks stay encrypted)        │
└────┬────────────────────────┬─────────────────────┬─────────┘
     │                        │                     │
     ▼                        ▼                     ▼
┌─────────────┐    ┌──────────────────┐   ┌────────────────┐
│Prerequisites│    │  Disk Discovery  │   │   Encryption   │
│  (prereqs.rs│    │   (disk/mod.rs)  │   │   (platform-   │
│             │    │                  │   │    specific)   │
│- Check TPM  │    │- Find all disks  │   │                │
│- Check OS   │    │- Filter data     │   │- LUKS2 (Linux) │
│- Validate   │    │  disks           │   │- BitLocker     │
│  tools      │    │- Get disk info   │   │  (Windows)     │
└─────────────┘    └──────────────────┘   └────────┬───────┘
                                                     │
                                                     ▼
                                            ┌────────────────┐
                                            │      TPM       │
                                            │  - Seal keys   │
                                            │  - Auto-unlock │
                                            └────────────────┘
```

### Module Organization

```
src/
├── main.rs              # Entry point and CLI
├── lib.rs               # Public library interface
├── handler.rs           # Extension lifecycle
├── disk/
│   └── mod.rs           # Disk discovery and info
├── prerequisites.rs     # VM validation
├── error.rs             # Error codes and types
├── logging.rs           # Tracing configuration
└── traits.rs            # Abstractions for DI/testing
```

## Design Principles

### 1. Separation of Concerns

Each module has a single, well-defined responsibility:

- **main.rs**: CLI argument parsing, routing to handlers
- **handler.rs**: Extension lifecycle management
- **disk/mod.rs**: Disk discovery and information
- **prerequisites.rs**: System validation
- **error.rs**: Error handling and codes
- **logging.rs**: Observability setup
- **traits.rs**: Abstractions for testing

### 2. Dependency Injection via Traits

Use traits to abstract external dependencies, enabling mocking in tests:

```rust
// Define trait in traits.rs
#[cfg_attr(test, mockall::automock)]
pub trait DiskDiscovery: Send + Sync {
    fn discover_disks(&self) -> Vec<DiskInfo>;
    fn is_data_disk(&self, disk: &DiskInfo) -> bool;
}

// Production implementation
pub struct SystemDiskDiscovery;

impl DiskDiscovery for SystemDiskDiscovery {
    fn discover_disks(&self) -> Vec<DiskInfo> {
        // Real implementation using sysinfo
    }
    
    fn is_data_disk(&self, disk: &DiskInfo) -> bool {
        // Real filtering logic
    }
}

// Use in handler
pub struct Handler {
    discovery: Box<dyn DiskDiscovery>,
}

impl Handler {
    pub fn new() -> Self {
        Self {
            discovery: Box::new(SystemDiskDiscovery),
        }
    }
    
    #[cfg(test)]
    pub fn with_discovery(discovery: Box<dyn DiskDiscovery>) -> Self {
        Self { discovery }
    }
}
```

**Available Traits:**
- `DiskDiscovery`: Disk enumeration and filtering
- `EncryptionProvider`: Encryption operations
- `TpmProvider`: TPM interactions
- `CommandRunner`: Command execution

### 3. Structured Error Handling

Use a well-defined error hierarchy with unique codes:

```rust
// Error structure
pub struct Error {
    code: ErrorCode,
    message: String,
    source: Option<Box<dyn std::error::Error + Send + Sync>>,
}

// Construction patterns
impl Error {
    // Simple error with code only
    pub fn new(code: ErrorCode) -> Self;
    
    // Error with custom message
    pub fn with_message(code: ErrorCode, message: impl Into<String>) -> Self;
    
    // Error wrapping another error
    pub fn with_source(code: ErrorCode, message: impl Into<String>, 
                       source: impl Into<Box<dyn std::error::Error + Send + Sync>>) -> Self;
}

// Usage
fn risky_operation() -> Result<()> {
    let file = File::open("config.json")
        .map_err(|e| Error::with_source(
            ErrorCode::ConfigFileNotFound,
            "Failed to open configuration file",
            e
        ))?;
    
    Ok(())
}
```

### 4. Type Safety and Newtype Pattern

Use type aliases and newtypes for clarity and safety:

```rust
// Type aliases for clarity
pub type Result<T> = std::result::Result<T, Error>;

// Newtype for type safety
pub struct DevicePath(PathBuf);

impl DevicePath {
    pub fn new(path: impl Into<PathBuf>) -> Result<Self> {
        let path = path.into();
        
        // Validation
        if !path.starts_with("/dev") {
            return Err(Error::with_message(
                ErrorCode::InvalidConfiguration,
                "Device path must start with /dev"
            ));
        }
        
        Ok(Self(path))
    }
    
    pub fn as_path(&self) -> &Path {
        &self.0
    }
}

// Usage prevents misuse
fn encrypt_disk(path: DevicePath) -> Result<()> {
    // path is guaranteed to be validated
    let device = path.as_path();
    // ...
}
```

### 5. Platform Abstraction

Handle platform differences explicitly:

```rust
// Platform-specific imports
#[cfg(target_os = "linux")]
use crate::linux::{LuksEncryption, SystemdCryptenroll};

#[cfg(target_os = "windows")]
use crate::windows::{BitLockerEncryption, TpmEnrollment};

// Platform-agnostic interface
pub trait PlatformEncryption {
    fn encrypt(&self, disk: &DiskInfo) -> Result<()>;
    fn is_encrypted(&self, disk: &DiskInfo) -> Result<bool>;
}

// Conditional compilation for implementations
#[cfg(target_os = "linux")]
pub fn get_platform_encryption() -> Box<dyn PlatformEncryption> {
    Box::new(LuksEncryption::new())
}

#[cfg(target_os = "windows")]
pub fn get_platform_encryption() -> Box<dyn PlatformEncryption> {
    Box::new(BitLockerEncryption::new())
}
```

## Extension Lifecycle Pattern

### State Machine

```
┌─────────┐
│ Initial │
└────┬────┘
     │
     │ install
     ▼
┌─────────┐
│Installed│◄────┐
└────┬────┘     │
     │          │ update
     │ enable   │
     ▼          │
┌─────────┐     │
│ Enabled │─────┘
└────┬────┘
     │
     │ disable
     ▼
┌─────────┐
│Disabled │
└────┬────┘
     │
     │ uninstall
     ▼
┌──────────┐
│ Removed  │
└──────────┘
```

### Handler Implementation Pattern

```rust
impl ExtensionHandler {
    #[instrument(skip(self), name = "install")]
    pub fn handle_install(&self) -> Result<()> {
        info!("Installing extension");
        
        // 1. Validate prerequisites
        self.validate_prerequisites()?;
        
        // 2. Create required directories
        self.create_directories()?;
        
        // 3. Initialize configuration
        self.init_config()?;
        
        info!("Installation complete");
        Ok(())
    }
    
    #[instrument(skip(self), name = "enable")]
    pub fn handle_enable(&self) -> Result<()> {
        info!("Enabling extension");
        
        // 1. Validate prerequisites (might have changed)
        self.validate_prerequisites()?;
        
        // 2. Discover data disks
        let disks = self.discover_data_disks()?;
        info!(disk_count = disks.len(), "Discovered disks");
        
        // 3. Encrypt each disk
        for disk in disks {
            self.encrypt_disk(&disk)?;
        }
        
        info!("Extension enabled successfully");
        Ok(())
    }
    
    #[instrument(skip(self), name = "disable")]
    pub fn handle_disable(&self) -> Result<()> {
        info!("Disabling extension (disks remain encrypted)");
        // Intentionally no-op: disks stay encrypted for security
        Ok(())
    }
}
```

## Data Flow Patterns

### 1. Disk Discovery Flow

```rust
pub fn discover_data_disks() -> Result<Vec<DiskInfo>> {
    // 1. Discover all disks (using sysinfo or platform APIs)
    let all_disks = discover_all_disks();
    
    // 2. Filter to data disks (exclude OS disk, removable media)
    let data_disks: Vec<DiskInfo> = all_disks
        .into_iter()
        .filter(is_data_disk)
        .collect();
    
    // 3. Validate disks are eligible for encryption
    let eligible_disks: Vec<DiskInfo> = data_disks
        .into_iter()
        .filter(|disk| !is_encrypted(disk).unwrap_or(false))
        .collect();
    
    if eligible_disks.is_empty() {
        return Err(Error::new(ErrorCode::NoDisksFound));
    }
    
    Ok(eligible_disks)
}
```

### 2. Encryption Flow

```rust
pub fn encrypt_disk(disk: &DiskInfo) -> Result<()> {
    // 1. Validate disk is not already encrypted
    if is_encrypted(disk)? {
        return Err(Error::new(ErrorCode::AlreadyEncrypted));
    }
    
    // 2. Generate encryption key on-VM
    let key = generate_encryption_key()?;
    
    // 3. Encrypt disk with platform-specific tool
    #[cfg(target_os = "linux")]
    encrypt_with_luks(disk, &key)?;
    
    #[cfg(target_os = "windows")]
    encrypt_with_bitlocker(disk, &key)?;
    
    // 4. Seal key to TPM for auto-unlock
    seal_key_to_tpm(&key)?;
    
    // 5. Securely zero key from memory
    secure_zero(&mut key);
    
    Ok(())
}
```

## Error Handling Patterns

### 1. Error Context Chain

```rust
pub fn process_disk(path: &str) -> Result<()> {
    // Lowest level: I/O error
    let metadata = std::fs::metadata(path)
        .map_err(|e| Error::with_source(
            ErrorCode::DiskReadFailed,
            format!("Failed to read disk metadata: {}", path),
            e
        ))?;
    
    // Mid level: Business logic error
    if metadata.len() == 0 {
        return Err(Error::with_message(
            ErrorCode::InvalidDiskState,
            format!("Disk is empty: {}", path)
        ));
    }
    
    // High level: Operation failed
    encrypt_disk(path)
        .map_err(|e| Error::with_source(
            ErrorCode::EncryptionFailed,
            format!("Failed to encrypt disk: {}", path),
            e
        ))?;
    
    Ok(())
}
```

### 2. Error Recovery Pattern

```rust
pub fn encrypt_all_disks(disks: &[DiskInfo]) -> Result<EncryptionSummary> {
    let mut summary = EncryptionSummary::default();
    
    for disk in disks {
        match encrypt_disk(disk) {
            Ok(_) => {
                info!(disk = disk.name, "Successfully encrypted");
                summary.success_count += 1;
            }
            Err(e) => {
                // Log but continue with other disks
                error!(disk = disk.name, error = %e, "Failed to encrypt");
                summary.failures.push((disk.name.clone(), e));
            }
        }
    }
    
    // Fail if no disks were encrypted successfully
    if summary.success_count == 0 {
        return Err(Error::new(ErrorCode::EncryptionFailed));
    }
    
    Ok(summary)
}
```

## Logging Patterns

### 1. Structured Logging with Tracing

```rust
use tracing::{info, warn, error, debug, instrument};

#[instrument(skip(self, disk), fields(disk_name = %disk.name))]
pub fn encrypt_disk(&self, disk: &DiskInfo) -> Result<()> {
    // Automatically logs function entry/exit with disk_name
    
    info!(size_gb = disk.total_space_gb(), "Starting encryption");
    
    let start = Instant::now();
    
    // ... encryption logic ...
    
    let duration = start.elapsed();
    info!(duration_ms = duration.as_millis(), "Encryption complete");
    
    Ok(())
}
```

### 2. Hierarchical Spans

```rust
#[instrument(name = "enable_extension")]
pub fn handle_enable(&self) -> Result<()> {
    info!("Extension enable started");
    
    let disks = self.discover_disks()?;
    
    for disk in disks {
        // Creates child span for each disk
        let _span = tracing::span!(tracing::Level::INFO, "encrypt_disk", 
                                   disk = %disk.name).entered();
        
        self.encrypt_disk(&disk)?;
    }
    
    info!("Extension enable completed");
    Ok(())
}
```

## Testing Patterns

### 1. Test Fixtures

```rust
#[cfg(test)]
mod test_fixtures {
    use super::*;
    
    pub fn create_test_disk(name: &str) -> DiskInfo {
        DiskInfo {
            name: name.to_string(),
            mount_point: PathBuf::from("/mnt/data"),
            file_system: "ext4".to_string(),
            disk_type: DiskType::SSD,
            total_space: 1_073_741_824,  // 1 GB
            available_space: 536_870_912,  // 512 MB
            is_removable: false,
        }
    }
    
    pub fn create_test_disks(count: usize) -> Vec<DiskInfo> {
        (0..count)
            .map(|i| create_test_disk(&format!("sd{}", (b'b' + i as u8) as char)))
            .collect()
    }
}
```

### 2. Mock Setup Pattern

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use mockall::predicate::*;
    
    fn setup_mock_discovery() -> MockDiskDiscovery {
        let mut mock = MockDiskDiscovery::new();
        
        mock.expect_discover_disks()
            .times(1)
            .returning(|| vec![
                create_test_disk("sdb"),
                create_test_disk("sdc"),
            ]);
        
        mock.expect_is_data_disk()
            .returning(|_| true);
        
        mock
    }
    
    #[test]
    fn test_handler_encrypts_discovered_disks() {
        let mock = setup_mock_discovery();
        let handler = Handler::with_discovery(Box::new(mock));
        
        let result = handler.handle_enable();
        assert!(result.is_ok());
    }
}
```

## Configuration Patterns

### 1. Builder Pattern for Complex Objects

```rust
pub struct EncryptionConfig {
    cipher: String,
    key_size: usize,
    hash: String,
    pbkdf: String,
}

pub struct EncryptionConfigBuilder {
    cipher: Option<String>,
    key_size: Option<usize>,
    hash: Option<String>,
    pbkdf: Option<String>,
}

impl EncryptionConfigBuilder {
    pub fn new() -> Self {
        Self {
            cipher: None,
            key_size: None,
            hash: None,
            pbkdf: None,
        }
    }
    
    pub fn cipher(mut self, cipher: impl Into<String>) -> Self {
        self.cipher = Some(cipher.into());
        self
    }
    
    pub fn key_size(mut self, size: usize) -> Self {
        self.key_size = Some(size);
        self
    }
    
    pub fn build(self) -> Result<EncryptionConfig> {
        Ok(EncryptionConfig {
            cipher: self.cipher.unwrap_or_else(|| "aes-xts-plain64".to_string()),
            key_size: self.key_size.unwrap_or(512),
            hash: self.hash.unwrap_or_else(|| "sha256".to_string()),
            pbkdf: self.pbkdf.unwrap_or_else(|| "argon2id".to_string()),
        })
    }
}

// Usage
let config = EncryptionConfigBuilder::new()
    .cipher("aes-xts-plain64")
    .key_size(512)
    .build()?;
```

## Performance Considerations

### 1. Avoid Unnecessary Allocations

```rust
// Good: Use string slices
pub fn process_device_name(name: &str) -> Result<()> {
    if name.starts_with("/dev/") {
        // ...
    }
    Ok(())
}

// Bad: Unnecessary allocation
pub fn process_device_name_bad(name: String) -> Result<()> {
    if name.starts_with("/dev/") {
        // ...
    }
    Ok(())
}
```

### 2. Lazy Evaluation

```rust
// Good: Lazy evaluation with closures
pub fn get_or_compute_expensive(&self) -> Result<String> {
    self.cached.clone()
        .or_else(|| {
            let result = expensive_computation();
            self.cached = Some(result.clone());
            Some(result)
        })
        .ok_or_else(|| Error::new(ErrorCode::ComputationFailed))
}
```

## Documentation Patterns

### 1. Module-Level Documentation

```rust
//! Disk discovery and information module.
//!
//! This module provides functionality for discovering and querying disk information
//! on both Linux and Windows platforms.
//!
//! # Examples
//!
//! ```no_run
//! use confidential_disk_encryption::disk::discover_disks;
//!
//! let disks = discover_disks();
//! for disk in disks {
//!     println!("Found disk: {} ({} GB)", disk.name, disk.total_space_gb());
//! }
//! ```
```

### 2. Function Documentation

```rust
/// Encrypts a disk using platform-native encryption with TPM-sealed keys.
///
/// This function performs the following steps:
/// 1. Validates the disk is not already encrypted
/// 2. Generates an encryption key on-VM
/// 3. Encrypts the disk with LUKS2 (Linux) or BitLocker (Windows)
/// 4. Seals the key to TPM for auto-unlock
///
/// # Arguments
///
/// * `disk` - Information about the disk to encrypt
///
/// # Returns
///
/// Returns `Ok(())` if encryption succeeds, or an error with code:
/// * `ErrorCode::AlreadyEncrypted` - Disk is already encrypted
/// * `ErrorCode::EncryptionFailed` - Encryption operation failed
/// * `ErrorCode::TpmError` - Failed to seal key to TPM
///
/// # Examples
///
/// ```no_run
/// # use confidential_disk_encryption::{disk::DiskInfo, encrypt_disk};
/// # let disk = DiskInfo { /* ... */ };
/// match encrypt_disk(&disk) {
///     Ok(_) => println!("Disk encrypted successfully"),
///     Err(e) => eprintln!("Encryption failed: {}", e),
/// }
/// ```
pub fn encrypt_disk(disk: &DiskInfo) -> Result<()> {
    // Implementation
}
```

## Summary

Key architectural principles:
- **Modularity**: Clear separation of concerns
- **Testability**: Dependency injection via traits
- **Type Safety**: Strong typing and newtypes
- **Error Handling**: Structured errors with context
- **Platform Abstraction**: Conditional compilation
- **Security**: Zero-trust key management
- **Observability**: Structured logging with tracing

When extending the codebase:
1. Follow existing patterns and conventions
2. Use traits for external dependencies
3. Add comprehensive tests
4. Document public APIs
5. Handle errors with appropriate codes
6. Use structured logging
7. Consider security implications
