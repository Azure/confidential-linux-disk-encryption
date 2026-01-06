# Confidential Disk Encryption Extension

A cross-platform Azure VM extension for confidential disk encryption, built in Rust.

## Overview

The Confidential Disk Encryption Extension provides secure disk encryption capabilities for Azure Virtual Machines running both Linux and Windows. This extension integrates with Azure's confidential computing infrastructure to enable encryption of VM disks with enhanced security guarantees.

## Features

- Cross-platform support (Linux and Windows)
- Disk discovery and enumeration
- Integration with platform-native encryption (LUKS on Linux, BitLocker on Windows)
- Azure VM extension compatibility

## Quick Start

### Prerequisites

- [Rust](https://rustup.rs/) (1.70 or later)
- Platform-specific requirements:
  - **Linux**: `cryptsetup` for LUKS support
  - **Windows**: BitLocker feature enabled

### Building

```bash
cargo build --release
```

### Running

```bash
# List available disks
cargo run
```

## Documentation

For detailed documentation, see the [docs/](docs/README.md) folder:

- [Architecture](docs/design/architecture.md) - System design and component overview
- [Requirements](docs/design/requirements.md) - Functional and non-functional requirements
- [Development Setup](docs/development/setup.md) - Getting started with development

## Project Structure

```
├── src/
│   ├── main.rs          # CLI entry point
│   ├── lib.rs           # Library root
│   ├── disk/            # Disk operations module
│   └── error.rs         # Error types
├── docs/                # Documentation
│   ├── design/          # Architecture and requirements
│   └── development/     # Development guides
└── tests/               # Integration tests
```

## License

See [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please see the [development setup guide](docs/development/setup.md) for getting started.
