# Testing Guidelines for Confidential Disk Encryption Extension

This document provides detailed testing guidelines for developers and GitHub Copilot when working on test code.

## Testing Philosophy

- **Test-Driven Development**: Write tests before or alongside implementation
- **High Coverage**: Target 80%+ code coverage, 100% for critical paths
- **Fast Tests**: Unit tests should be fast; use mocks for I/O and external dependencies
- **Deterministic**: Tests must be reproducible and not flaky
- **Clear Assertions**: Each test should verify one specific behavior

## Test Organization

### Unit Tests (Colocated)

Unit tests live in the same file as the code they test, inside `#[cfg(test)]` modules:

```rust
// src/my_module.rs

pub fn calculate_sum(a: i32, b: i32) -> i32 {
    a + b
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_calculate_sum_positive_numbers() {
        assert_eq!(calculate_sum(2, 3), 5);
    }

    #[test]
    fn test_calculate_sum_negative_numbers() {
        assert_eq!(calculate_sum(-2, -3), -5);
    }

    #[test]
    fn test_calculate_sum_mixed() {
        assert_eq!(calculate_sum(5, -3), 2);
    }
}
```

### Integration Tests

Integration tests go in the `tests/` directory and test the public API:

```rust
// tests/cli_integration.rs

use assert_cmd::Command;
use predicates::prelude::*;

#[test]
fn test_dry_run_command() {
    Command::cargo_bin("cde")
        .unwrap()
        .arg("dry-run")
        .assert()
        .success()
        .stdout(predicate::str::contains("Discovering disks"));
}

#[test]
fn test_invalid_command_fails() {
    Command::cargo_bin("cde")
        .unwrap()
        .arg("invalid-command")
        .assert()
        .failure()
        .stderr(predicate::str::contains("Unknown command"));
}
```

## Test Naming Conventions

### Pattern

```rust
#[test]
fn test_<function_name>_<scenario>() { }
```

### Examples

```rust
// Good: Descriptive and specific
#[test]
fn test_disk_info_calculates_usage_percent() { }

#[test]
fn test_is_data_disk_excludes_root_partition() { }

#[test]
fn test_error_from_io_preserves_message() { }

#[test]
fn test_prerequisite_check_fails_when_tpm_missing() { }

// Bad: Too vague
#[test]
fn test_disk() { }

#[test]
fn test_works() { }

#[test]
fn test1() { }
```

## Testing Patterns

### 1. Testing Success Paths

```rust
#[test]
fn test_encrypt_disk_succeeds() {
    let disk = create_test_disk("/dev/sdb", 1_073_741_824);
    let result = encrypt_disk(&disk);
    
    assert!(result.is_ok());
}
```

### 2. Testing Error Conditions

```rust
#[test]
fn test_encrypt_disk_fails_on_readonly() {
    let readonly_disk = create_readonly_disk();
    let result = encrypt_disk(&readonly_disk);
    
    assert!(result.is_err());
    let err = result.unwrap_err();
    assert_eq!(err.code, ErrorCode::DiskReadFailed);
}
```

### 3. Testing Edge Cases

```rust
#[test]
fn test_disk_usage_percent_with_zero_space() {
    let disk = DiskInfo {
        total_space: 0,
        available_space: 0,
        // ...
    };
    
    assert_eq!(disk.usage_percent(), 0.0);
}

#[test]
fn test_disk_usage_percent_fully_used() {
    let disk = DiskInfo {
        total_space: 1_000_000,
        available_space: 0,
        // ...
    };
    
    assert_eq!(disk.usage_percent(), 100.0);
}
```

### 4. Testing with Fixtures

Use helper functions for common test data:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    fn create_test_disk(name: &str, size: u64) -> DiskInfo {
        DiskInfo {
            name: name.to_string(),
            mount_point: PathBuf::from("/mnt/data"),
            file_system: "ext4".to_string(),
            disk_type: DiskType::SSD,
            total_space: size,
            available_space: size / 2,
            is_removable: false,
        }
    }

    #[test]
    fn test_using_fixture() {
        let disk = create_test_disk("sdb", 1_073_741_824);
        assert_eq!(disk.name, "sdb");
    }
}
```

### 5. Testing with rstest (Parameterized Tests)

```rust
use rstest::rstest;

#[rstest]
#[case("/", false)]
#[case("/boot", false)]
#[case("/boot/efi", false)]
#[case("/mnt/data", true)]
#[case("/home", true)]
fn test_is_data_disk_various_paths(#[case] path: &str, #[case] expected: bool) {
    let disk = create_test_disk_with_mount(path);
    let discovery = SystemDiskDiscovery;
    assert_eq!(discovery.is_data_disk(&disk), expected);
}
```

## Mocking with mockall

### Defining Mockable Traits

```rust
// In traits.rs or module file
#[cfg_attr(test, mockall::automock)]
pub trait DiskDiscovery: Send + Sync {
    fn discover_disks(&self) -> Vec<DiskInfo>;
    fn is_data_disk(&self, disk: &DiskInfo) -> bool;
}
```

### Using Mocks in Tests

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use mockall::predicate::*;

    #[test]
    fn test_handler_uses_disk_discovery() {
        // Create mock
        let mut mock_discovery = MockDiskDiscovery::new();
        
        // Set expectations
        mock_discovery
            .expect_discover_disks()
            .times(1)
            .returning(|| vec![
                create_test_disk("sdb", 1_073_741_824),
                create_test_disk("sdc", 2_147_483_648),
            ]);
        
        mock_discovery
            .expect_is_data_disk()
            .times(2)
            .returning(|_| true);
        
        // Use mock
        let handler = Handler::new(Box::new(mock_discovery));
        let result = handler.process_disks();
        
        assert!(result.is_ok());
    }

    #[test]
    fn test_mock_with_specific_arguments() {
        let mut mock = MockCommandRunner::new();
        
        mock.expect_run_command()
            .with(eq("cryptsetup"), eq(vec!["--version".to_string()]))
            .times(1)
            .returning(|_, _| Ok(CommandOutput {
                status: 0,
                stdout: "cryptsetup 2.3.0".to_string(),
                stderr: String::new(),
            }));
        
        let runner = mock;
        let output = runner.run_command("cryptsetup", vec!["--version".to_string()]);
        assert!(output.is_ok());
    }
}
```

## Testing CLI with assert_cmd

### Basic CLI Tests

```rust
use assert_cmd::Command;
use predicates::prelude::*;

#[test]
fn test_cli_help() {
    Command::cargo_bin("cde")
        .unwrap()
        .arg("--help")
        .assert()
        .success()
        .stdout(predicate::str::contains("Usage"));
}

#[test]
fn test_cli_version() {
    Command::cargo_bin("cde")
        .unwrap()
        .arg("--version")
        .assert()
        .success();
}
```

### Testing Exit Codes

```rust
#[test]
fn test_invalid_command_returns_failure() {
    Command::cargo_bin("cde")
        .unwrap()
        .arg("invalid")
        .assert()
        .failure()
        .code(1);
}
```

### Testing Output

```rust
#[test]
fn test_check_prereqs_output() {
    Command::cargo_bin("cde")
        .unwrap()
        .arg("check-prereqs")
        .assert()
        .success()
        .stdout(predicate::str::contains("Prerequisite Check Summary"))
        .stdout(predicate::str::contains("TPM"));
}
```

## Testing with Temporary Files

```rust
use tempfile::TempDir;

#[test]
fn test_reads_config_file() {
    let temp_dir = TempDir::new().unwrap();
    let config_path = temp_dir.path().join("config.json");
    
    std::fs::write(&config_path, r#"{"enabled": true}"#).unwrap();
    
    let config = read_config(&config_path).unwrap();
    assert!(config.enabled);
}

#[test]
fn test_creates_log_directory() {
    let temp_dir = TempDir::new().unwrap();
    let log_dir = temp_dir.path().join("logs");
    
    create_log_directory(&log_dir).unwrap();
    
    assert!(log_dir.exists());
    assert!(log_dir.is_dir());
}
```

## Test Coverage Requirements

### Critical Paths (100% coverage)

- Key generation and sealing
- Disk encryption operations
- TPM interactions
- Error handling in handlers

### Standard Paths (80%+ coverage)

- Disk discovery
- Configuration parsing
- Logging setup
- Prerequisite checks

### What to Test

✅ **DO Test:**
- Public APIs and functions
- Error conditions and edge cases
- Platform-specific behavior
- Integration between modules
- CLI commands and output

❌ **DON'T Test:**
- External library internals
- Obvious getters/setters (unless they have logic)
- Generated code
- Private implementation details (test through public API)

## Running Tests

### Development

```bash
# Run all tests
cargo nextest run

# Run tests with output
cargo nextest run --no-capture

# Run specific test
cargo nextest run test_disk_info_calculations

# Run tests in a module
cargo nextest run disk

# Watch mode (with cargo-watch)
cargo watch -x "nextest run"
```

### CI Environment

```bash
# CI profile (defined in .config/nextest.toml)
cargo nextest run --profile ci

# With coverage
cargo llvm-cov nextest
```

### Performance

```bash
# Release mode (faster execution)
cargo nextest run --release

# Parallel execution (default in nextest)
cargo nextest run --jobs 4
```

## Debugging Tests

### Print Debug Output

```rust
#[test]
fn test_with_debug() {
    let disk = create_test_disk("sdb", 1_000_000);
    println!("Disk: {:?}", disk);  // Shows with --no-capture
    
    assert_eq!(disk.total_space, 1_000_000);
}
```

### Run with RUST_LOG

```bash
RUST_LOG=debug cargo nextest run test_name --no-capture
```

### Use dbg! macro

```rust
#[test]
fn test_with_dbg() {
    let result = calculate_something();
    dbg!(&result);  // Prints value and continues
    assert!(result > 0);
}
```

## Common Testing Anti-Patterns

❌ **Avoid:**

```rust
// Testing multiple things in one test
#[test]
fn test_everything() {
    test_disk_discovery();
    test_encryption();
    test_cleanup();
}

// Flaky tests with sleep
#[test]
fn test_async_operation() {
    start_operation();
    std::thread::sleep(Duration::from_secs(1));  // BAD
    assert!(is_complete());
}

// Tests depending on each other
static mut STATE: i32 = 0;
#[test]
fn test_1() {
    unsafe { STATE = 42; }
}
#[test]
fn test_2() {
    unsafe { assert_eq!(STATE, 42); }  // BAD: depends on test_1
}

// Incomplete error testing
#[test]
fn test_error() {
    let result = operation();
    assert!(result.is_err());  // Should also check error type/message
}
```

✅ **Prefer:**

```rust
// One test per behavior
#[test]
fn test_disk_discovery_finds_data_disks() {
    // Test only disk discovery
}

// Deterministic tests
#[test]
fn test_async_operation() {
    let result = operation().wait();  // Proper synchronization
    assert!(result.is_ok());
}

// Independent tests
#[test]
fn test_independent() {
    let state = setup_local_state();
    assert_eq!(state.value, 42);
}

// Complete error testing
#[test]
fn test_error_details() {
    let result = operation();
    assert!(result.is_err());
    let err = result.unwrap_err();
    assert_eq!(err.code, ErrorCode::Expected);
    assert!(err.message.contains("expected text"));
}
```

## Test Documentation

Add doc comments to tests when the behavior being tested is not obvious:

```rust
/// Test that disk usage percentage is correctly calculated as a value
/// between 0.0 and 100.0, even when the disk is empty or full.
#[test]
fn test_disk_usage_percent_boundary_conditions() {
    // Test implementation
}
```

## Continuous Testing

During development:

1. Run tests frequently (after each small change)
2. Use cargo-watch for automatic test running
3. Fix failing tests before adding new features
4. Keep test runtime fast (< 1 second for unit tests)
5. Use `--no-capture` to debug failures

```bash
# Auto-run tests on file changes
cargo install cargo-watch
cargo watch -x "nextest run"
```

## Summary Checklist

When writing tests, ensure:

- [ ] Tests are in the correct location (colocated or `tests/`)
- [ ] Test names follow the `test_<function>_<scenario>` pattern
- [ ] Each test verifies one specific behavior
- [ ] Success paths, error paths, and edge cases are covered
- [ ] External dependencies are mocked
- [ ] Tests are deterministic and don't rely on timing
- [ ] Tests are independent (can run in any order)
- [ ] CLI tests use `assert_cmd` with proper assertions
- [ ] Error tests verify error codes and messages
- [ ] Tests run quickly (use mocks for slow operations)
