# Azure VM Encryption Extension - Tests

Simple test setup and execution for the Azure Linux VM Encryption Extension.

## Prerequisites

- Open PowerShell or Command Prompt
- Navigate to the test directory: `cd VMEncryption/main/test`

## Setup

1. Install dependencies:
```bash
py -m pip install -r ../../requirements.txt
```

## Running Tests

All commands should be run from the `VMEncryption/main/test` directory.

Run all tests:
```bash
py -m pytest
```

Run specific test file:
```bash
py -m pytest test_azurelinuxPatching.py
```

Run tests with verbose output:
```bash
py -m pytest -v
```

Run specific test method:
```bash
py -m pytest test_azurelinuxPatching.py::Test_azurelinuxPatching::test_install_cryptsetup_already_installed -v
```

That's it! The `conftest.py` file handles all Python path configuration automatically.