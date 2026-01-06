# Requirements

This document outlines the functional and non-functional requirements for the Confidential Disk Encryption Extension.

## Project Goals

1. Provide a reliable, cross-platform disk encryption solution for Azure VMs
2. Integrate seamlessly with Azure's confidential computing infrastructure
3. Support both Linux and Windows operating systems
4. Use platform-native encryption technologies for maximum compatibility

## Functional Requirements

### FR-1: Disk Discovery

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1.1 | The system shall enumerate all available disks on the VM | Must Have |
| FR-1.2 | The system shall identify disk type (OS, data, temporary) | Must Have |
| FR-1.3 | The system shall report disk size, filesystem, and mount point | Must Have |
| FR-1.4 | The system shall detect current encryption status of each disk | Should Have |

### FR-2: Disk Encryption

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-2.1 | The system shall encrypt data disks using platform-native encryption | Must Have |
| FR-2.2 | The system shall support LUKS encryption on Linux | Must Have |
| FR-2.3 | The system shall support BitLocker encryption on Windows | Must Have |
| FR-2.4 | The system shall support encryption key retrieval from Azure Key Vault | Must Have |
| FR-2.5 | The system shall support OS disk encryption | Should Have |

### FR-3: Azure Integration

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-3.1 | The system shall implement the Azure VM extension interface | Must Have |
| FR-3.2 | The system shall report operation status to Azure | Must Have |
| FR-3.3 | The system shall parse extension configuration from Azure | Must Have |
| FR-3.4 | The system shall support extension enable/disable/update operations | Must Have |

### FR-4: Operations

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-4.1 | The system shall validate disks before encryption | Must Have |
| FR-4.2 | The system shall provide detailed error messages on failure | Must Have |
| FR-4.3 | The system shall support dry-run mode for testing | Should Have |
| FR-4.4 | The system shall log all operations for troubleshooting | Must Have |

## Non-Functional Requirements

### NFR-1: Performance

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-1.1 | Disk discovery shall complete within 5 seconds | 5s |
| NFR-1.2 | Extension initialization shall complete within 30 seconds | 30s |
| NFR-1.3 | The binary size shall be minimized for fast deployment | < 10MB |

### NFR-2: Reliability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-2.1 | The system shall handle transient failures with retry logic | 3 retries |
| NFR-2.2 | The system shall not corrupt data on failure | 0 data loss |
| NFR-2.3 | The system shall recover gracefully from interruptions | Resumable |

### NFR-3: Security

| ID | Requirement | Description |
|----|-------------|-------------|
| NFR-3.1 | Encryption keys shall never be written to disk in plaintext | Critical |
| NFR-3.2 | The system shall validate all inputs to prevent injection attacks | Critical |
| NFR-3.3 | The system shall run with minimal required privileges | Important |
| NFR-3.4 | Logs shall not contain sensitive information | Critical |

### NFR-4: Compatibility

| ID | Requirement | Description |
|----|-------------|-------------|
| NFR-4.1 | Support Ubuntu 20.04, 22.04, 24.04 LTS | Linux |
| NFR-4.2 | Support RHEL 8, 9 | Linux |
| NFR-4.3 | Support Windows Server 2019, 2022 | Windows |
| NFR-4.4 | Support Windows 10, 11 (for development) | Windows |

### NFR-5: Maintainability

| ID | Requirement | Description |
|----|-------------|-------------|
| NFR-5.1 | Code shall be modular and well-documented | Maintainability |
| NFR-5.2 | All public APIs shall have documentation comments | Documentation |
| NFR-5.3 | Test coverage shall be maintained above 80% | Testing |
| NFR-5.4 | Code shall follow Rust style guidelines (rustfmt) | Style |

## Constraints

1. **Language**: Implementation must be in Rust for safety and performance
2. **Dependencies**: Minimize external dependencies to reduce attack surface
3. **Licensing**: All dependencies must have compatible open-source licenses
4. **Platform APIs**: Use platform-native encryption tools rather than reimplementing encryption

## Out of Scope (v1.0)

The following features are explicitly out of scope for the initial release:

- Full disk encryption for running VMs (only pre-boot encryption)
- Custom encryption algorithms
- Encryption key escrow beyond Azure Key Vault
- GUI or web interface
- Support for non-Azure cloud platforms

## Success Criteria

The project will be considered successful when:

1. ✅ Disk discovery works on both Linux and Windows
2. ⬜ Data disk encryption works using LUKS (Linux) and BitLocker (Windows)
3. ⬜ Extension can be deployed via Azure and report status correctly
4. ⬜ All "Must Have" requirements are implemented and tested
5. ⬜ Documentation is complete and accurate
