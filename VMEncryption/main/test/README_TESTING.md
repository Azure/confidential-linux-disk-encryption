# Test Configuration for Azure Disk Encryption Extension

## Running Unit Tests

This directory contains unit tests for the Azure Disk Encryption Extension. The tests are designed to run in a Linux environment but include compatibility handling for cross-platform development.

### Prerequisites

- Python 3.6+
- Required packages (install via pip):
  - mock
  - packaging
  - pytest (optional, for alternative test runner)

### Running Tests

#### Option 1: Using the provided script (Linux/WSL)
```bash
./run_tests.sh
```

#### Option 2: Manual execution
```bash
cd VMEncryption/main
export PYTHONPATH="$(pwd):../../Utils:../../Common:$PYTHONPATH"
python3 -m unittest discover test -v
```

#### Option 3: CI/CD Pipeline
The tests are automatically run in the OneBranch.Official.yml pipeline when the `runUnitTests` parameter is set to `true` (default).

### Test Categories

1. **Platform-specific tests**: Tests that require Linux-specific tools (lsblk, cryptsetup, etc.)
2. **Cross-platform tests**: Tests that work on both Windows and Linux
3. **Mock-based tests**: Tests that use mocked dependencies

### Known Issues

- Some tests may fail on Windows due to missing Linux utilities
- fcntl module is not available on Windows (handled gracefully)
- Path separator differences between Windows and Linux

### Test Results Interpretation

- **PASS**: Test completed successfully
- **FAIL**: Test logic failed (needs investigation)
- **ERROR**: Import or setup error (usually platform-related)

For CI/CD environments, all tests should pass in the Linux container environment.
