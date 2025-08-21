import sys
import os

# Get the directory containing this conftest.py file
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))

# Get the main directory (parent of test directory)
_MAIN_DIR = os.path.dirname(_THIS_DIR)

# Add the main directory to Python path so we can import modules
sys.path.insert(0, _MAIN_DIR)

# Add the VMEncryption directory to Python path for patch modules
_VM_ENCRYPTION_DIR = os.path.dirname(_MAIN_DIR)
sys.path.insert(0, _VM_ENCRYPTION_DIR)

# Add the Utils directory for utility modules
_UTILS_DIR = os.path.join(os.path.dirname(_VM_ENCRYPTION_DIR), 'Utils')
sys.path.insert(0, _UTILS_DIR)

# Add the SinglePass root directory
_SINGLEPASS_DIR = os.path.dirname(_VM_ENCRYPTION_DIR)
sys.path.insert(0, _SINGLEPASS_DIR)

# Print debug info to help troubleshoot import issues
print(f"conftest.py: Added to sys.path:")
print(f"  Main dir: {_MAIN_DIR}")
print(f"  VMEncryption dir: {_VM_ENCRYPTION_DIR}")
print(f"  Utils dir: {_UTILS_DIR}")
print(f"  SinglePass dir: {_SINGLEPASS_DIR}")
