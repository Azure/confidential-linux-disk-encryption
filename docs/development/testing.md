# Testing Guide

This document describes the testing strategy and how to run tests for the Confidential Disk Encryption Extension.

## Testing Stack

| Tool | Purpose |
|------|---------|
| `cargo test` | Built-in test runner |
| `mockall` | Mocking traits for unit tests |
| `rstest` | Fixtures and parameterized tests |
| `assert_cmd` | CLI integration testing |
| `predicates` | Assertions for CLI output |
| `tempfile` | Temporary files/directories for tests |

## Running Tests

### All Tests

```bash
cargo test
```

### Unit Tests Only

```bash
cargo test --lib
```

### Integration Tests Only

```bash
cargo test --test cli_integration
```

### With Output

```bash
cargo test -- --nocapture
```

### Single Test

```bash
cargo test test_name
```

## Test Organization

```
src/
├── disk/mod.rs          # Unit tests in #[cfg(test)] mod tests
├── error.rs             # Error handling tests
├── handler.rs           # Handler logic tests with mocks
├── logging.rs           # Logging configuration tests
└── traits.rs            # Trait implementation tests

tests/
└── cli_integration.rs   # End-to-end CLI tests
```

## Unit Testing with Mocks

The codebase uses traits for external dependencies, making it easy to mock them in tests.

### Available Mock Traits

| Trait | Mock | Purpose |
|-------|------|---------|
| `DiskDiscovery` | `MockDiskDiscovery` | Mock disk enumeration |
| `EncryptionProvider` | `MockEncryptionProvider` | Mock encryption operations |
| `TpmProvider` | `MockTpmProvider` | Mock TPM availability/enrollment |
| `CommandRunner` | `MockCommandRunner` | Mock shell command execution |

### Example: Mocking Disk Discovery

```rust
use confidential_disk_encryption::traits::MockDiskDiscovery;
use confidential_disk_encryption::disk::{DiskInfo, DiskType};
use std::path::PathBuf;

#[test]
fn test_with_mock_disks() {
    let mut mock_discovery = MockDiskDiscovery::new();
    
    // Set up mock to return specific disks
    mock_discovery
        .expect_discover_disks()
        .returning(|| {
            vec![
                DiskInfo {
                    name: "sda1".to_string(),
                    mount_point: PathBuf::from("/"),
                    file_system: "ext4".to_string(),
                    disk_type: DiskType::SSD,
                    total_space: 100_000_000_000,
                    available_space: 50_000_000_000,
                    is_removable: false,
                },
                DiskInfo {
                    name: "sdb1".to_string(),
                    mount_point: PathBuf::from("/mnt/data"),
                    file_system: "ext4".to_string(),
                    disk_type: DiskType::HDD,
                    total_space: 500_000_000_000,
                    available_space: 400_000_000_000,
                    is_removable: false,
                },
            ]
        });
    
    // Use mock in your test
    let disks = mock_discovery.discover_disks();
    assert_eq!(disks.len(), 2);
}
```

### Example: Mocking Command Execution

```rust
use confidential_disk_encryption::traits::{MockCommandRunner, CommandOutput};

#[test]
fn test_with_mock_commands() {
    let mut mock_runner = MockCommandRunner::new();
    
    // Mock 'cryptsetup' command exists
    mock_runner
        .expect_command_exists()
        .with(mockall::predicate::eq("cryptsetup"))
        .returning(|_| true);
    
    // Mock command execution
    mock_runner
        .expect_run_command()
        .returning(|_, _| {
            Ok(CommandOutput {
                status: 0,
                stdout: "success".to_string(),
                stderr: String::new(),
            })
        });
    
    assert!(mock_runner.command_exists("cryptsetup"));
}
```

## Parameterized Tests with rstest

Use `rstest` for data-driven tests:

```rust
use rstest::rstest;

#[rstest]
#[case("/", false)]           // Root mount - not a data disk
#[case("/boot", false)]       // Boot mount - not a data disk
#[case("/mnt/data", true)]    // Data mount - is a data disk
#[case("C:\\", false)]        // Windows C: - not a data disk
#[case("D:\\Data", true)]     // Windows D: - is a data disk
fn test_is_data_disk(#[case] mount_point: &str, #[case] expected: bool) {
    let discovery = SystemDiskDiscovery;
    let disk = create_test_disk(mount_point, false);
    assert_eq!(discovery.is_data_disk(&disk), expected);
}
```

## Integration Testing

Integration tests in `tests/` directory test the CLI binary end-to-end.

### Testing CLI Output

```rust
use assert_cmd::Command;
use predicates::prelude::*;

#[test]
fn test_cli_output() {
    Command::cargo_bin("cde")
        .unwrap()
        .arg("dry-run")
        .assert()
        .success()
        .stdout(predicate::str::contains("Extension invoked"));
}
```

### Testing CLI Failure

```rust
#[test]
fn test_cli_failure() {
    Command::cargo_bin("cde")
        .unwrap()
        .arg("invalid-command")
        .assert()
        .failure()
        .stderr(predicate::str::contains("Unknown command"));
}
```

## Test Fixtures

For tests that need temporary files or directories:

```rust
use tempfile::{tempdir, NamedTempFile};

#[test]
fn test_with_temp_dir() {
    let dir = tempdir().unwrap();
    let file_path = dir.path().join("test.txt");
    
    std::fs::write(&file_path, "test content").unwrap();
    
    assert!(file_path.exists());
    // dir is automatically cleaned up when dropped
}
```

## Coverage Goals

| Module | Target |
|--------|--------|
| `error.rs` | 100% |
| `disk/mod.rs` | 90%+ |
| `handler.rs` | 85%+ |
| `logging.rs` | 80%+ |
| `traits.rs` | 90%+ |
| **Overall** | 85%+ |

## Continuous Integration

Tests should be run in CI on every pull request:

```yaml
# Example GitHub Actions workflow
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - run: cargo test --all-features
```

## Best Practices

1. **Test behavior, not implementation** - Focus on what the code does, not how
2. **Use descriptive test names** - `test_encryption_fails_when_disk_busy` > `test_error`
3. **One assertion per test** (when practical) - Makes failures easier to diagnose
4. **Keep tests fast** - Unit tests should run in milliseconds
5. **Test edge cases** - Empty lists, very large values, error conditions
6. **Use mocks for external dependencies** - Don't hit real disks/TPM/network in unit tests
7. **Clean up after tests** - Use `tempfile` for automatic cleanup

## Troubleshooting

### Tests Hang

If tests hang, check for:
- Infinite loops in mocked methods
- Missing mock expectations (mockall panics)
- File locks not released

### Flaky Tests

If tests pass sometimes and fail others:
- Check for race conditions
- Ensure no shared mutable state between tests
- Use `cargo test -- --test-threads=1` to run sequentially

### Mock Not Called

If you get "MockXxx was not called" errors:
- Ensure the mock is actually used in the code path
- Check that expectations match the actual calls (arguments, call count)
