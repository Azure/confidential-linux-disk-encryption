# Testing

## Test Runner

We use [cargo-nextest](https://nexte.st/) for better test output and faster parallel execution.

### Install nextest

```bash
cargo install cargo-nextest --locked
```

### Run Tests

```bash
# Run all tests (recommended)
cargo nextest run

# Run with verbose output
cargo nextest run --no-capture

# Run specific test
cargo nextest run test_disk_info_calculations

# Run tests matching pattern
cargo nextest run disk

# Run in release mode
cargo nextest run --release
```

### Standard cargo test

If you prefer the standard test runner:

```bash
cargo test

# Quiet mode (just summary)
cargo test -q
```

## Test Organization

Tests are colocated with source code (Rust best practice):

```
src/
├── disk/mod.rs       # 16 unit tests
├── error.rs          # 25 unit tests  
├── handler.rs        # 22 unit tests
├── prerequisites.rs  # 27 unit tests
├── traits.rs         # 8 unit tests
├── logging.rs        # 2 unit tests
tests/
└── cli_integration.rs  # 8 integration tests
```

**Total: 112 tests**

## Test Categories

### Unit Tests (colocated)

Test individual functions and internal logic:

```rust
// src/disk/mod.rs
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_disk_info_calculations() {
        let disk = DiskInfo { ... };
        assert_eq!(disk.used_space(), 536_870_912);
    }
}
```

### Integration Tests (`tests/`)

Test public API from external perspective:

```rust
// tests/cli_integration.rs
use assert_cmd::Command;

#[test]
fn test_dry_run_succeeds() {
    Command::cargo_bin("cde")
        .arg("dry-run")
        .assert()
        .success();
}
```

## Writing Tests

### Naming Convention

```rust
#[test]
fn test_<function>_<scenario>() { }

// Examples:
fn test_disk_info_zero_space() { }
fn test_is_data_disk_excludes_root() { }
fn test_error_from_io_various_kinds() { }
```

### Test Helpers

Create helpers for repeated setup:

```rust
fn create_test_disk(name: &str, mount_point: &str) -> DiskInfo {
    DiskInfo {
        name: name.to_string(),
        mount_point: PathBuf::from(mount_point),
        // ...
    }
}
```

### Testing Errors

```rust
#[test]
fn test_operation_fails_with_error_code() {
    let result = some_operation();
    assert!(result.is_err());
    
    let err = result.unwrap_err();
    assert_eq!(err.code, ErrorCode::NoDisksFound);
}
```

## CI Testing

CI uses nextest with the `ci` profile:

```yaml
- name: Run tests
  run: cargo nextest run --profile ci
```

The CI profile (`.config/nextest.toml`):
- Retries flaky tests once
- Shows failures immediately
- Runs all tests (no fail-fast)

## Coverage

To generate coverage reports:

```bash
cargo install cargo-llvm-cov
cargo llvm-cov nextest
