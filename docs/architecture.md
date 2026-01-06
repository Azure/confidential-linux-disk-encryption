# Architecture

## Overview

Azure VM extension that encrypts all data disks using platform-native encryption.

```
Azure Platform
    │
    ▼
Extension Handler (install/enable/disable/update/uninstall)
    │
    ├── Prerequisites Check
    ├── Disk Discovery
    └── Encryption Engine
            │
            ├── LUKS2 (Linux)
            └── BitLocker (Windows)
```

## Components

| Component | File | Purpose |
|-----------|------|---------|
| Handler | `handler.rs` | Extension lifecycle management |
| Disk Discovery | `disk/mod.rs` | Find and enumerate disks |
| Prerequisites | `prerequisites.rs` | Validate VM can encrypt |
| Error | `error.rs` | Structured error codes |
| Logging | `logging.rs` | Tracing-based logging |
| Traits | `traits.rs` | Abstractions for testing |

## Extension Lifecycle

| Command | When | Action |
|---------|------|--------|
| `install` | Deployed to VM | Validate prerequisites |
| `enable` | Extension enabled | Encrypt all data disks |
| `disable` | Extension disabled | No-op (disks stay encrypted) |
| `update` | Version change | Migrate if needed |
| `uninstall` | Extension removed | No-op (disks stay encrypted) |

## Encryption

### Linux
- **Tool**: `cryptsetup` with LUKS2
- **Auto-unlock**: systemd-cryptenroll + TPM2

### Windows
- **Tool**: BitLocker (`manage-bde`)
- **Auto-unlock**: TPM protector

## Key Management

```
┌─────────────────┐
│   Extension     │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐  ┌──────────┐
│  TPM  │  │ Key Vault│
└───────┘  └──────────┘
 Primary    Fallback
```

1. **TPM (primary)**: Key sealed to VM's vTPM
2. **Key Vault (fallback)**: For VMs without TPM

## Data Flow

```
1. Azure calls: cde enable
2. Handler validates prerequisites
3. Disk discovery finds data disks
4. For each disk:
   a. Generate encryption key
   b. Encrypt with LUKS2/BitLocker
   c. Enroll TPM for auto-unlock
   d. Store backup in Key Vault
5. Report status to Azure
```

## Files

```
/var/lib/waagent/Microsoft.Azure.Security.ConfidentialDiskEncryption/
├── config/           # Extension settings
├── status/           # Status reported to Azure
└── logs/             # → /var/log/azure/confidential-disk-encryption/
