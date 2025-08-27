# Azure VM Encryption Extension - Test Suite

Unit tests for the Azure Linux VM Encryption Extension. Tests ensure cross-platform compatibility (Python 2.7/3.x) across multiple Linux distributions.

## Quick Start

```bash
# Navigate to the repository root
cd "c:/path/to/confidential-linux-disk-encryption"

# Run VMEncryption tests (407 tests)
python -m pytest VMEncryption/main/test/ -v

# Run Utils tests (5 tests)  
python -m pytest Utils/test/ -v

# Run all tests separately (412 total)
python -m pytest VMEncryption/main/test/ -v && python -m pytest Utils/test/ -v

# Run with coverage
python -m pytest VMEncryption/main/test/ -v --cov=VMEncryption/main --cov-report=term-missing
```

## Setup

Create and activate a virtual environment, then install dependencies:
```bash
# Create virtual environment (from repository root)
python -m venv vmencryption-test-env

# Activate (Windows)
vmencryption-test-env\Scripts\activate

# Activate (Linux/macOS)
source vmencryption-test-env/bin/activate

# Install dependencies
pip install pytest pytest-cov coverage cryptography pytz
```

## Updated Test Commands

**From repository root (`confidential-linux-disk-encryption/`):**

```bash
# Set Python path (Windows PowerShell)
$env:PYTHONPATH = "$PWD\VMEncryption\main;$PWD\VMEncryption;$PWD\Utils;$PWD"

# Set Python path (Windows CMD)
set PYTHONPATH=%CD%\VMEncryption\main;%CD%\VMEncryption;%CD%\Utils;%CD%

# Set Python path (Linux/macOS)
export PYTHONPATH="$PWD/VMEncryption/main:$PWD/VMEncryption:$PWD/Utils:$PWD"

# Run all tests
python -m pytest VMEncryption/main/test/ Utils/test/ -v

# Run with coverage
python -m pytest VMEncryption/main/test/ -v --cov=VMEncryption/main --cov-report=term-missing

# Run specific test module
python -m pytest VMEncryption/main/test/test_azurelinuxPatching.py -v

# Run individual test
python -m pytest VMEncryption/main/test/test_azurelinuxPatching.py::Test_azurelinuxPatching::test_install_cryptsetup_already_installed -v
```


## GitHub Actions / CI Commands

**For use in GitHub Actions workflows:**

```yaml
# Install dependencies
- name: Install test dependencies
  run: pip install pytest pytest-cov coverage cryptography pytz

# Set Python path
- name: Set up Python path
  run: echo "PYTHONPATH=${{ github.workspace }}/VMEncryption/main:${{ github.workspace }}/VMEncryption:${{ github.workspace }}/Utils:${{ github.workspace }}" >> $GITHUB_ENV

# Run tests with coverage
- name: Run VMEncryption tests
  working-directory: VMEncryption
  run: python -m pytest main/test/ -v --cov=main --cov-report=term-missing --cov-report=xml:coverage.xml

- name: Run Utils tests  
  working-directory: Utils
  run: python -m pytest test/ -v
```

### Using GitHub Copilot

This codebase includes Copilot instructions at `../.copilot-instructions.md`. To generate tests for new code:

1. Open the file you want to test
2. Type a comment like: `# @copilot generate unit tests for this class`
3. Copilot will generate tests following the project's patterns and Python 2.7/3.x compatibility

The instructions ensure generated tests include proper mocking, cross-platform compatibility, and follow established patterns.
