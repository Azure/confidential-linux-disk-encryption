# Security Model

This document describes how the extension handles encryption keys to ensure customers never need to trust Microsoft with their keys.

## Zero-Trust Principles

1. **Keys generated on-VM** - Never transmitted to or from Azure
2. **Keys sealed to TPM** - Cannot be extracted, even by Microsoft
3. **No key escrow** - Microsoft never has access to keys
4. **Open source** - All code is auditable

## Key Generation

Keys are generated locally on the VM using cryptographically secure random number generators:

| Platform | Source |
|----------|--------|
| Linux | `/dev/urandom` (kernel CSPRNG) |
| Windows | `BCryptGenRandom` (CNG) |

The extension never:
- Receives keys from external sources
- Transmits keys to any endpoint
- Stores keys anywhere except the TPM

## Key Storage

Keys are sealed to the VM's TPM:

```
┌─────────────────┐
│   Encryption    │
│      Key        │
└────────┬────────┘
         │ Seal
         ▼
┌─────────────────┐
│      vTPM       │  ← Key can only be unsealed on this VM
└─────────────────┘
```

### TPM Sealing Guarantees

- **Same VM**: Key can only be unsealed on the same VM
- **Same boot chain**: TPM PCRs ensure boot integrity
- **Confidential VMs**: Key additionally bound to attestation state

### What This Means

- Microsoft cannot extract keys from the TPM
- Even with VM access, keys cannot be recovered without the TPM
- If the VM is moved/cloned, sealed keys become inaccessible

## Key Recovery

**By design, there is no recovery mechanism.**

| Scenario | Outcome |
|----------|---------|
| TPM failure | Data unrecoverable |
| VM re-imaging | Data unrecoverable |
| VM migration | Keys re-sealed to new TPM |

### Customer Responsibility

If customers need key backup:
- They must implement their own backup strategy
- They can export recovery keys before sealing to TPM
- This is explicitly outside the extension's scope

## Telemetry

### What IS Collected
- Error codes (e.g., `CDE200`)
- Operation timing (encryption duration)
- Disk counts (number of disks encrypted)
- Success/failure status

### What is NOT Collected
- Encryption keys or key material
- Disk contents or metadata
- Customer data of any kind
- Key derivation parameters

## Threat Model

| Threat | Mitigation |
|--------|------------|
| Microsoft accesses keys | Keys never leave VM, sealed to TPM |
| Malicious extension update | Open source, auditable, signed releases |
| Host compromise | Confidential VMs provide memory encryption |
| Key exfiltration | TPM prevents key extraction |

## Verification

Customers can verify:

1. **Code audit**: Extension is open source
2. **TPM state**: `tpm2_getcap` shows key is sealed
3. **No network**: Extension makes no outbound connections for keys
4. **Build reproducibility**: Binaries can be rebuilt from source
