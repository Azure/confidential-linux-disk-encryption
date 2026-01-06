# Boot-Time Disk Unlock

Encrypted disks must be unlocked at boot without user interaction.

## Strategy

```
┌─────────────────┐
│   VM Boot       │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐  ┌──────────┐
│  TPM  │  │ Key Vault│
└───────┘  └──────────┘
 Primary    Fallback
```

## Linux (systemd-cryptenroll + TPM2)

### Requirements
- systemd 248+
- TPM2 device (`/dev/tpm0` or `/dev/tpmrm0`)
- LUKS2 formatted disk

### Enrollment
```bash
# Enroll TPM2 for auto-unlock
systemd-cryptenroll --tpm2-device=auto /dev/sdb

# Verify
systemd-cryptenroll /dev/sdb
```

### Boot Process
1. systemd starts `cryptsetup` target
2. TPM2 unseals the key (requires same boot chain)
3. Disk unlocked automatically

### Fallback
If TPM unavailable:
1. Extension stores key in Azure Key Vault
2. Boot script fetches key via managed identity
3. Manual unlock with fetched key

## Windows (BitLocker + TPM)

### Requirements
- TPM 1.2+ (TPM 2.0 recommended)
- BitLocker enabled

### Enrollment
```powershell
# TPM protector (auto-unlock)
Add-BitLockerKeyProtector -MountPoint "D:" -TpmProtector

# Recovery key (backup to Key Vault)
Add-BitLockerKeyProtector -MountPoint "D:" -RecoveryPasswordProtector
```

### Boot Process
1. Boot loader measures system state
2. TPM unseals BitLocker key
3. Disk unlocked automatically

## Confidential VM Considerations

| VM Type | TPM Available | Notes |
|---------|--------------|-------|
| Standard | No | Use Key Vault fallback |
| Trusted Launch | Yes (vTPM) | Full auto-unlock |
| Confidential | Yes (vTPM) | Key bound to VM attestation |
