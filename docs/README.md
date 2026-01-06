# Documentation

## Quick Reference

| Topic | Description |
|-------|-------------|
| [Architecture](architecture.md) | System design and components |
| [Security Model](security.md) | Zero-trust key handling |
| [Error Codes](error-codes.md) | All CDE### error codes |
| [Logging](logging.md) | Log configuration and locations |
| [Testing](testing.md) | Running and writing tests |

## Operations

| Topic | Description |
|-------|-------------|
| [Encryption](operations/encryption.md) | LUKS2 and BitLocker encryption |
| [Boot Unlock](operations/boot-unlock.md) | TPM-based auto-unlock |

## Getting Started

```bash
# Clone and build
git clone https://github.com/Azure/confidential-linux-disk-encryption.git
cd confidential-linux-disk-encryption
cargo build

# Run tests
cargo test

# Dry run (development)
cargo run -- dry-run

# Check prerequisites
cargo run -- check-prereqs
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `install` | Validate prerequisites |
| `enable` | Encrypt all data disks |
| `disable` | Disable extension (disks stay encrypted) |
| `update` | Handle version updates |
| `uninstall` | Remove extension (disks stay encrypted) |
| `dry-run` | Show what would be encrypted |
| `check-prereqs` | Validate VM meets requirements |

## VM Requirements

**Trusted Launch or Confidential VM required** - Standard VMs are not supported (no vTPM).
