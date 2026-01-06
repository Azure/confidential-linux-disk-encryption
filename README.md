# Confidential Disk Encryption Extension

[![CI](https://github.com/Azure/confidential-linux-disk-encryption/actions/workflows/ci.yml/badge.svg)](https://github.com/Azure/confidential-linux-disk-encryption/actions/workflows/ci.yml)

A cross-platform Azure VM extension for confidential disk encryption, built in Rust.

## Overview

The Confidential Disk Encryption Extension automatically encrypts all data disks attached to an Azure Virtual Machine using platform-native encryption with TPM-sealed keys:

- **Linux**: LUKS2 via `cryptsetup` + TPM2
- **Windows**: BitLocker via `manage-bde` + TPM

**Requires Trusted Launch or Confidential VM** (provides vTPM).

## Security

This extension is designed so customers never need to trust Microsoft with their encryption keys:

| Principle | Implementation |
|-----------|----------------|
| **Keys generated on-VM** | Uses OS CSPRNG, never transmitted |
| **Keys sealed to TPM** | Cannot be extracted, even by Microsoft |
| **No key escrow** | No Key Vault, no external storage |
| **Open source** | All code is auditable |

See [Security Model](docs/security.md) for details.

## Features

- **Automatic encryption**: All data disks encrypted when extension is enabled
- **Cross-platform**: Supports Linux and Windows VMs
- **TPM-sealed keys**: Keys never leave the VM
- **Platform-native**: Uses LUKS2 and BitLocker
- **Idempotent**: Safe to run multiple times

## VM Requirements

| VM Type | Supported | Notes |
|---------|-----------|-------|
| Standard | ❌ | No vTPM |
| Trusted Launch | ✅ | vTPM available |
| Confidential | ✅ | vTPM + memory encryption |

## Installation

The extension is installed via Azure:

### Azure CLI
```bash
az vm extension set \
  --resource-group myResourceGroup \
  --vm-name myVM \
  --name ConfidentialDiskEncryption \
  --publisher Microsoft.Azure.Security \
  --version 1.0
```

### Azure Portal
Navigate to VM → Extensions → Add → Confidential Disk Encryption

## Development

### Prerequisites

- [Rust](https://rustup.rs/) 1.70+
- **Linux**: `cryptsetup`, `systemd` 248+
- **Windows**: BitLocker feature

### Building

```bash
cargo build --release
```

### Testing

```bash
# Run all tests
cargo test

# Dry run (shows what would be encrypted)
cargo run -- dry-run

# Check prerequisites
cargo run -- check-prereqs
```

## Documentation

See [docs/](docs/README.md):

| Topic | Description |
|-------|-------------|
| [Architecture](docs/architecture.md) | System design |
| [Security Model](docs/security.md) | Zero-trust key handling |
| [Error Codes](docs/error-codes.md) | CDE### error reference |
| [Testing](docs/testing.md) | Test guide |

## Project Structure

```
├── src/
│   ├── main.rs          # Entry point
│   ├── handler.rs       # Extension lifecycle
│   ├── disk/mod.rs      # Disk discovery
│   ├── prerequisites.rs # VM validation
│   ├── error.rs         # Error codes
│   └── logging.rs       # Tracing
├── docs/                # Documentation
└── tests/               # Integration tests
```

## License

See [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Run `cargo test` before submitting PRs.
