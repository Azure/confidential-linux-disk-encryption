# Architecture

## Overview

Azure VM extension that encrypts all data disks using platform-native encryption with TPM-sealed keys.

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
            ├── LUKS2 + TPM (Linux)
            └── BitLocker + TPM (Windows)
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

Keys are generated on-VM and sealed to the TPM:

```
┌─────────────────┐
│  Key Generation │  ← On-VM CSPRNG
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│      vTPM       │  ← Key sealed, never leaves VM
└─────────────────┘
```

- **No key escrow** - Microsoft never has access to keys
- **TPM-only** - Requires Trusted Launch or Confidential VM
- **No recovery** - If TPM fails, data is unrecoverable by design

See [Security Model](security.md) for details.

## Data Flow

```
1. Azure calls: cde enable
2. Handler validates prerequisites (including TPM)
3. Disk discovery finds data disks
4. For each disk:
   a. Generate encryption key on-VM
   b. Encrypt with LUKS2/BitLocker
   c. Seal key to TPM
5. Report status to Azure
```

## VM Requirements

| VM Type | Supported | Notes |
|---------|-----------|-------|
| Standard | ❌ | No vTPM |
| Trusted Launch | ✅ | vTPM available |
| Confidential | ✅ | vTPM + memory encryption |

## Files

```
/var/lib/waagent/Microsoft.Azure.Security.ConfidentialDiskEncryption/
├── config/           # Extension settings
├── status/           # Status reported to Azure
└── logs/             # → /var/log/azure/confidential-disk-encryption/
