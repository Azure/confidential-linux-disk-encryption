# Testing

## Run Tests

```bash
cargo test              # All tests
cargo test --lib        # Unit tests only
cargo test test_name    # Single test
cargo test -- --nocapture  # Show output
```

## Test Structure

```
src/
├── *.rs              # Unit tests in #[cfg(test)] mod tests
tests/
└── cli_integration.rs  # CLI integration tests
```

## Mocking

Traits enable mocking external dependencies:

| Trait | Purpose |
|-------|---------|
| `DiskDiscovery` | Disk enumeration |
| `EncryptionProvider` | Encryption operations |
| `TpmProvider` | TPM operations |
| `CommandRunner` | Shell commands |

```rust
use confidential_disk_encryption::traits::MockDiskDiscovery;

#[test]
fn test_with_mocks() {
    let mut mock = MockDiskDiscovery::new();
    mock.expect_discover_disks().returning(|| vec![/* test data */]);
    
    let disks = mock.discover_disks();
    assert_eq!(disks.len(), 1);
}
```

## CLI Testing

```rust
use assert_cmd::Command;
use predicates::prelude::*;

#[test]
fn test_cli_success() {
    Command::cargo_bin("cde").unwrap()
        .arg("dry-run")
        .assert()
        .success();
}

#[test]
fn test_cli_failure() {
    Command::cargo_bin("cde").unwrap()
        .arg("invalid")
        .assert()
        .failure()
        .stderr(predicate::str::contains("Unknown command"));
}
```

## CI

Tests run on every PR via GitHub Actions:
- Ubuntu and Windows
- `cargo test --all-features`
- `cargo clippy`
- `cargo fmt --check`
