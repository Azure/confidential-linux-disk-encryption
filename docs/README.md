# Documentation

Welcome to the Confidential Disk Encryption Extension documentation.

## Contents

### Design

- [Architecture](design/architecture.md) - System architecture, components, and how they interact
- [Requirements](design/requirements.md) - Functional and non-functional requirements
- [Linux Encryption](design/linux-encryption.md) - Linux encryption options (LUKS, cryptsetup, systemd-cryptenroll)
- [Boot Unlock](design/boot-unlock.md) - How encrypted disks are automatically unlocked at boot (TPM, Key Vault)

### Development

- [Setup](development/setup.md) - How to set up your development environment

## Getting Started

If you're new to the project, we recommend reading the documents in this order:

1. **[Requirements](design/requirements.md)** - Understand what we're building and why
2. **[Architecture](design/architecture.md)** - Learn how the system is designed
3. **[Setup](development/setup.md)** - Get your environment ready to contribute

## Document Conventions

- Design documents describe *what* and *why*
- Development documents describe *how*
- All documents should be kept up-to-date as the project evolves
