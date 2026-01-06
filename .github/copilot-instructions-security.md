# Security Guidelines for Confidential Disk Encryption Extension

This document provides security-specific guidelines for developing and reviewing code in this project. **Security is paramount** - this extension handles encryption keys and customer data.

## Security Principles

### 1. Zero-Trust Key Management

**Core Principle**: Customers never need to trust Microsoft with their encryption keys.

#### Key Generation
- ✅ **DO**: Generate keys on-VM using OS CSPRNG
  - Linux: `/dev/urandom` (kernel CSPRNG)
  - Windows: `BCryptGenRandom` (CNG)
- ❌ **DON'T**: Accept keys from external sources
- ❌ **DON'T**: Use weak random sources (timestamp, PID, etc.)
- ❌ **DON'T**: Derive keys from predictable data

```rust
// Good: Use OS CSPRNG
#[cfg(target_os = "linux")]
fn generate_key() -> Result<Vec<u8>> {
    let mut key = vec![0u8; 32];
    let mut file = File::open("/dev/urandom")?;
    file.read_exact(&mut key)?;
    Ok(key)
}

// Bad: Predictable key generation
fn generate_weak_key() -> Vec<u8> {
    let timestamp = SystemTime::now().duration_since(UNIX_EPOCH).unwrap();
    timestamp.as_secs().to_le_bytes().to_vec()  // NEVER DO THIS
}
```

#### Key Storage
- ✅ **DO**: Seal keys to TPM immediately after generation
- ✅ **DO**: Verify TPM is available before generating keys
- ❌ **DON'T**: Store keys in files, environment variables, or memory longer than necessary
- ❌ **DON'T**: Transmit keys over network
- ❌ **DON'T**: Log keys or key material

```rust
// Good: Seal to TPM immediately
pub fn encrypt_disk(disk: &DiskInfo, tpm: &dyn TpmProvider) -> Result<()> {
    // Generate key
    let key = generate_key()?;
    
    // Use key immediately
    encrypt_with_key(disk, &key)?;
    
    // Seal to TPM
    tpm.seal_key(&key)?;
    
    // Clear key from memory
    secure_zero(&mut key);
    
    Ok(())
}

// Bad: Key stored in struct
pub struct BadEncryptionHandler {
    encryption_key: Vec<u8>,  // NEVER DO THIS
}
```

#### Key Lifecycle
- Generate → Use → Seal to TPM → Zero memory
- Never store keys in retrievable form outside TPM
- No key escrow, no recovery mechanism by design

### 2. Secure Command Execution

**Threat**: Command injection vulnerabilities

#### Input Validation
- ✅ **DO**: Validate all inputs before using in commands
- ✅ **DO**: Use explicit paths for binaries
- ✅ **DO**: Use parameterized execution (not shell strings)
- ❌ **DON'T**: Concatenate user input into shell commands
- ❌ **DON'T**: Use `sh -c` with untrusted input

```rust
// Good: Validated parameters
pub fn encrypt_disk_safe(device_path: &str) -> Result<()> {
    // Validate input
    if !device_path.starts_with("/dev/") {
        return Err(Error::new(ErrorCode::InvalidConfiguration));
    }
    
    // Use explicit path and separate arguments
    Command::new("/usr/sbin/cryptsetup")
        .arg("luksFormat")
        .arg(device_path)
        .arg("--type")
        .arg("luks2")
        .output()?;
    
    Ok(())
}

// Bad: Command injection vulnerability
pub fn encrypt_disk_unsafe(device_path: &str) -> Result<()> {
    // VULNERABLE: User input in shell command
    Command::new("sh")
        .arg("-c")
        .arg(format!("cryptsetup luksFormat {}", device_path))  // NEVER DO THIS
        .output()?;
    
    Ok(())
}
```

#### Sanitization Rules
```rust
/// Validates that a device path is safe for use in commands
pub fn validate_device_path(path: &str) -> Result<()> {
    // Must start with /dev/
    if !path.starts_with("/dev/") {
        return Err(Error::with_message(
            ErrorCode::InvalidConfiguration,
            "Device path must start with /dev/"
        ));
    }
    
    // Must not contain shell metacharacters
    let dangerous_chars = ['|', '&', ';', '>', '<', '`', '$', '(', ')', '{', '}'];
    if path.chars().any(|c| dangerous_chars.contains(&c)) {
        return Err(Error::with_message(
            ErrorCode::InvalidConfiguration,
            "Device path contains invalid characters"
        ));
    }
    
    // Must be canonical (no ../ or ./)
    let canonical = std::fs::canonicalize(path)?;
    if !canonical.starts_with("/dev") {
        return Err(Error::with_message(
            ErrorCode::InvalidConfiguration,
            "Device path must be in /dev/"
        ));
    }
    
    Ok(())
}
```

### 3. Secure Logging and Telemetry

**Threat**: Leaking sensitive information through logs

#### What to Log
- ✅ **DO**: Log operation status (success/failure)
- ✅ **DO**: Log error codes (e.g., `CDE200`)
- ✅ **DO**: Log operation timing (performance metrics)
- ✅ **DO**: Log disk names and mount points
- ✅ **DO**: Log command names (not full commands with args)

#### What NOT to Log
- ❌ **DON'T**: Log encryption keys or key material
- ❌ **DON'T**: Log key derivation parameters
- ❌ **DON'T**: Log disk contents or file data
- ❌ **DON'T**: Log customer data
- ❌ **DON'T**: Log full command lines with sensitive args
- ❌ **DON'T**: Log passphrases or secrets

```rust
// Good: Safe logging
use tracing::{info, error};

pub fn encrypt_disk(disk: &DiskInfo, key: &[u8]) -> Result<()> {
    info!(disk = disk.name, "Starting disk encryption");
    
    let result = perform_encryption(disk, key);
    
    match result {
        Ok(_) => {
            info!(disk = disk.name, "Disk encryption completed");
            Ok(())
        }
        Err(e) => {
            error!(disk = disk.name, error_code = ?e.code, "Encryption failed");
            Err(e)
        }
    }
}

// Bad: Leaking sensitive data
pub fn encrypt_disk_unsafe(disk: &DiskInfo, key: &[u8]) -> Result<()> {
    info!("Encrypting disk {} with key {:?}", disk.name, key);  // NEVER LOG KEYS
    
    let command = format!("cryptsetup luksFormat {} --key-file -", disk.name);
    info!("Running: {}", command);  // OK - no sensitive args
    
    // ... but if we logged the key file contents, that would be bad
    
    Ok(())
}
```

#### Telemetry Guidelines
```rust
/// Safe telemetry event
pub struct EncryptionTelemetry {
    pub error_code: Option<ErrorCode>,
    pub duration_ms: u64,
    pub disk_count: usize,
    pub success: bool,
    // NO keys, NO disk contents, NO customer data
}

impl EncryptionTelemetry {
    pub fn to_json(&self) -> String {
        serde_json::json!({
            "error_code": self.error_code.map(|c| c.to_string()),
            "duration_ms": self.duration_ms,
            "disk_count": self.disk_count,
            "success": self.success,
        }).to_string()
    }
}
```

### 4. Memory Security

**Threat**: Keys left in memory after use

#### Secure Memory Handling
```rust
use std::ptr;

/// Securely zero memory containing sensitive data
pub fn secure_zero(data: &mut [u8]) {
    unsafe {
        ptr::write_volatile(data.as_mut_ptr(), 0);
        ptr::write_bytes(data.as_mut_ptr(), 0, data.len());
    }
}

/// Wrapper that zeros memory on drop
pub struct SecureBytes {
    data: Vec<u8>,
}

impl SecureBytes {
    pub fn new(data: Vec<u8>) -> Self {
        Self { data }
    }
    
    pub fn as_slice(&self) -> &[u8] {
        &self.data
    }
}

impl Drop for SecureBytes {
    fn drop(&mut self) {
        secure_zero(&mut self.data);
    }
}

// Usage
pub fn use_key_safely() -> Result<()> {
    let key_data = generate_key()?;
    let key = SecureBytes::new(key_data);
    
    // Use key
    encrypt_with_key(key.as_slice())?;
    
    // Key automatically zeroed when dropped
    Ok(())
}
```

### 5. Error Handling and Information Disclosure

**Threat**: Error messages revealing sensitive information

#### Safe Error Messages
```rust
// Good: Generic error messages
pub fn open_encrypted_disk(path: &str) -> Result<()> {
    let result = cryptsetup_open(path);
    
    match result {
        Ok(_) => Ok(()),
        Err(e) => {
            // Don't reveal whether disk exists, key is wrong, etc.
            Err(Error::with_message(
                ErrorCode::EncryptionFailed,
                "Failed to open encrypted disk"
            ))
        }
    }
}

// Bad: Revealing sensitive information
pub fn open_encrypted_disk_unsafe(path: &str, key: &[u8]) -> Result<()> {
    if !Path::new(path).exists() {
        return Err(Error::new("Disk not found"));  // Reveals existence
    }
    
    let result = cryptsetup_open_with_key(path, key);
    if result.is_err() {
        return Err(Error::new("Invalid key"));  // Confirms key validity
    }
    
    Ok(())
}
```

### 6. Time-of-Check to Time-of-Use (TOCTOU)

**Threat**: File system race conditions

```rust
// Good: Use file descriptors, not paths
pub fn read_secure_file(path: &Path) -> Result<String> {
    use std::os::unix::fs::PermissionsExt;
    
    // Open file and get descriptor
    let file = File::open(path)?;
    
    // Check permissions on the opened file descriptor
    let metadata = file.metadata()?;
    let permissions = metadata.permissions();
    
    if permissions.mode() & 0o077 != 0 {
        return Err(Error::with_message(
            ErrorCode::InvalidConfiguration,
            "File has insecure permissions"
        ));
    }
    
    // Read from the same file descriptor
    let mut contents = String::new();
    BufReader::new(file).read_to_string(&mut contents)?;
    
    Ok(contents)
}

// Bad: TOCTOU vulnerability
pub fn read_secure_file_unsafe(path: &Path) -> Result<String> {
    // Check permissions
    let metadata = std::fs::metadata(path)?;
    if metadata.permissions().readonly() {
        // File could be modified between check and read
    }
    
    // Read file (different operation)
    let contents = std::fs::read_to_string(path)?;  // TOCTOU race
    
    Ok(contents)
}
```

### 7. Cryptographic Best Practices

#### Algorithm Selection
- ✅ **DO**: Use LUKS2 (not LUKS1) on Linux
- ✅ **DO**: Use AES-256 for encryption
- ✅ **DO**: Use strong KDF (PBKDF2, Argon2)
- ❌ **DON'T**: Use deprecated algorithms (DES, RC4, MD5)
- ❌ **DON'T**: Roll your own crypto

```rust
/// Recommended LUKS2 format options
pub fn format_luks2_secure(device: &str) -> Result<()> {
    Command::new("/usr/sbin/cryptsetup")
        .arg("luksFormat")
        .arg("--type").arg("luks2")
        .arg("--cipher").arg("aes-xts-plain64")
        .arg("--key-size").arg("512")  // 256-bit key (512 bits for XTS)
        .arg("--hash").arg("sha256")
        .arg("--pbkdf").arg("argon2id")
        .arg("--pbkdf-memory").arg("1048576")  // 1GB
        .arg("--pbkdf-parallel").arg("4")
        .arg(device)
        .output()?;
    
    Ok(())
}
```

### 8. TPM Security

**Threat**: Unsealing keys on wrong VM or after compromise

#### TPM PCR Policy
```rust
/// Seal key to TPM with PCR policy
pub fn seal_to_tpm_secure(key: &[u8], pcrs: &[u32]) -> Result<()> {
    // Seal to specific PCRs (boot integrity)
    // Common PCRs:
    // - PCR 0: BIOS/UEFI code
    // - PCR 7: Secure Boot state
    // - PCR 14: Boot authority policy
    
    tpm2_seal(key, pcrs)?;
    
    Ok(())
}
```

### 9. Dependency Security

#### Dependency Review
Before adding dependencies:
- [ ] Check for known vulnerabilities (cargo-audit)
- [ ] Review the crate's security history
- [ ] Verify the crate is actively maintained
- [ ] Check the crate's dependencies
- [ ] Prefer crates from trusted sources

```bash
# Install cargo-audit
cargo install cargo-audit

# Check for vulnerabilities
cargo audit
```

#### Lock File
- ✅ **DO**: Commit `Cargo.lock` to track exact versions
- ✅ **DO**: Regularly update dependencies (`cargo update`)
- ✅ **DO**: Review dependency updates in PRs

### 10. Testing Security Properties

```rust
#[cfg(test)]
mod security_tests {
    use super::*;

    #[test]
    fn test_key_not_logged() {
        let key = vec![1, 2, 3, 4];
        let log_output = capture_logs(|| {
            encrypt_with_key(&key).unwrap();
        });
        
        // Ensure key bytes not in logs
        assert!(!log_output.contains("1, 2, 3, 4"));
        assert!(!log_output.contains(&format!("{:?}", key)));
    }

    #[test]
    fn test_device_path_validation() {
        // Valid paths
        assert!(validate_device_path("/dev/sdb").is_ok());
        assert!(validate_device_path("/dev/nvme0n1").is_ok());
        
        // Invalid paths (command injection attempts)
        assert!(validate_device_path("/dev/sdb; rm -rf /").is_err());
        assert!(validate_device_path("/dev/sdb|cat /etc/passwd").is_err());
        assert!(validate_device_path("../../etc/passwd").is_err());
    }

    #[test]
    fn test_memory_zeroed_on_drop() {
        let mut key_data = vec![0xAA; 32];
        let key_ptr = key_data.as_ptr();
        
        {
            let key = SecureBytes::new(key_data);
            // Use key
        } // Drop happens here
        
        // Check memory is zeroed (may not work due to optimization)
        // In practice, use tools like valgrind with --track-origins=yes
        unsafe {
            let slice = std::slice::from_raw_parts(key_ptr, 32);
            assert!(slice.iter().all(|&b| b == 0));
        }
    }
}
```

## Security Review Checklist

When reviewing code or PRs, verify:

- [ ] No encryption keys in logs, errors, or telemetry
- [ ] Keys generated with CSPRNG (not predictable sources)
- [ ] Keys sealed to TPM immediately after use
- [ ] Memory containing keys is securely zeroed
- [ ] No key transmission over network
- [ ] No key storage in files or persistent storage
- [ ] Command execution uses validated inputs
- [ ] No shell injection vulnerabilities (`sh -c` with user input)
- [ ] Error messages don't reveal sensitive information
- [ ] File operations avoid TOCTOU races
- [ ] Strong cryptographic algorithms (LUKS2, AES-256)
- [ ] Dependencies checked for vulnerabilities
- [ ] Tests verify security properties
- [ ] Telemetry collects only safe metrics

## Reporting Security Issues

If you discover a security vulnerability:

1. **DO NOT** create a public GitHub issue
2. Report to Microsoft Security Response Center (MSRC)
3. Provide detailed information including:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

## Additional Resources

- [OWASP Secure Coding Practices](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/)
- [Rust Security Guidelines](https://anssi-fr.github.io/rust-guide/)
- [TPM 2.0 Specification](https://trustedcomputinggroup.org/resource/tpm-library-specification/)
- [LUKS Specification](https://gitlab.com/cryptsetup/cryptsetup/-/wikis/LUKS-standard/on-disk-format.pdf)
