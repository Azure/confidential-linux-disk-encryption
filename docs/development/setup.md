# Development Setup

This guide will help you set up your development environment for the Confidential Disk Encryption Extension.

## Prerequisites

### All Platforms

1. **Rust Toolchain** (1.70 or later)
   ```bash
   # Install rustup (Rust toolchain manager)
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   
   # Or on Windows, download from https://rustup.rs
   ```

2. **Git**
   ```bash
   # Verify installation
   git --version
   ```

### Linux-Specific

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install build-essential pkg-config libssl-dev

# RHEL/CentOS/Fedora
sudo dnf groupinstall "Development Tools"
sudo dnf install openssl-devel
```

### Windows-Specific

1. **Visual Studio Build Tools** (or Visual Studio with C++ workload)
   - Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Select "Desktop development with C++"

2. **Windows SDK** (usually included with Visual Studio Build Tools)

## Getting Started

### Clone the Repository

```bash
git clone https://github.com/Azure/confidential-linux-disk-encryption.git
cd confidential-linux-disk-encryption
```

### Build the Project

```bash
# Debug build (faster compilation, includes debug symbols)
cargo build

# Release build (optimized)
cargo build --release
```

### Run the Application

```bash
# Run directly
cargo run

# Run with arguments (when implemented)
cargo run -- --help
```

### Run Tests

```bash
# Run all tests
cargo test

# Run tests with output
cargo test -- --nocapture

# Run a specific test
cargo test test_name
```

## Development Workflow

### Code Formatting

We use `rustfmt` for consistent code formatting:

```bash
# Format all code
cargo fmt

# Check formatting without making changes
cargo fmt -- --check
```

### Linting

We use `clippy` for linting:

```bash
# Run clippy
cargo clippy

# Run clippy and fail on warnings (used in CI)
cargo clippy -- -D warnings
```

### Documentation

Generate and view documentation:

```bash
# Generate docs
cargo doc

# Generate and open in browser
cargo doc --open
```

## IDE Setup

### Visual Studio Code

Recommended extensions:

1. **rust-analyzer** - Rust language support
2. **CodeLLDB** - Debugger for Rust
3. **Even Better TOML** - TOML file support
4. **Error Lens** - Inline error display

`.vscode/settings.json` (recommended):
```json
{
    "rust-analyzer.checkOnSave.command": "clippy",
    "editor.formatOnSave": true,
    "[rust]": {
        "editor.defaultFormatter": "rust-lang.rust-analyzer"
    }
}
```

### JetBrains IDEs (RustRover, CLion, IntelliJ)

1. Install the Rust plugin
2. Configure the toolchain in Settings → Languages & Frameworks → Rust

## Cross-Platform Development

### Building for Linux on Windows

Using WSL (Windows Subsystem for Linux):

```bash
# Install WSL if needed
wsl --install

# Inside WSL, install Rust and build
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
cd /mnt/c/path/to/project
cargo build
```

### Building for Windows on Linux

```bash
# Install Windows target
rustup target add x86_64-pc-windows-gnu

# Install MinGW
sudo apt install mingw-w64

# Cross-compile
cargo build --target x86_64-pc-windows-gnu
```

## Project Structure

```
src/
├── main.rs          # CLI entry point
├── lib.rs           # Library root (exports public modules)
├── disk/
│   └── mod.rs       # Disk operations module
└── error.rs         # Error types

tests/
└── disk_tests.rs    # Integration tests
```

## Troubleshooting

### Common Issues

**Build fails with linker errors on Windows**
- Ensure Visual Studio Build Tools are installed with C++ workload
- Try running from "Developer Command Prompt for VS"

**Build fails with OpenSSL errors on Linux**
- Install OpenSSL development packages (see Prerequisites)

**Clippy warnings in CI**
- Run `cargo clippy` locally and fix warnings before pushing

### Getting Help

1. Check existing GitHub issues
2. Review the [Architecture](../design/architecture.md) document
3. Ask in the project's discussion forum

## Next Steps

After setting up your environment:

1. Read the [Architecture](../design/architecture.md) document
2. Review the [Requirements](../design/requirements.md)
3. Look at open issues labeled `good first issue`
4. Make your first contribution!
