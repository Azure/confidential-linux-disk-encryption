# Boot-Time Disk Unlock

Encrypted disks are automatically unlocked at boot using TPM-sealed keys.

## Requirements

| Platform | Requirements |
|----------|--------------|
| Linux | systemd 248+, vTPM (`/dev/tpm0`), LUKS2 |
| Windows | vTPM, BitLocker enabled |

**VM Type**: Trusted Launch or Confidential VM required (provides vTPM)

## Linux (systemd-cryptenroll + TPM2)

### Enrollment
```bash
# Enroll TPM2 for auto-unlock
systemd-cryptenroll --tpm2-device=auto /dev/sdb

# Verify enrollment
systemd-cryptenroll /dev/sdb
```

### Boot Process
1. systemd starts `cryptsetup` target
2. TPM2 unseals the key (requires same boot chain)
3. Disk unlocked automatically

### Verification
```bash
# Check TPM is available
ls /dev/tpm*

# Check disk enrollment
systemd-cryptenroll /dev/sdb
```

## Windows (BitLocker + TPM)

### Enrollment
```powershell
# Enable BitLocker with TPM protector
Enable-BitLocker -MountPoint "D:" -TpmProtector
```

### Boot Process
1. Boot loader measures system state to TPM PCRs
2. TPM unseals BitLocker key
3. Disk unlocked automatically

### Verification
```powershell
# Check TPM status
Get-Tpm

# Check BitLocker status
manage-bde -status D:
```

## No TPM = No Encryption

VMs without vTPM cannot use this extension:

| VM Type | vTPM | Supported |
|---------|------|-----------|
| Standard | ❌ | ❌ |
| Trusted Launch | ✅ | ✅ |
| Confidential | ✅ | ✅ |

If TPM is not available, the extension fails with error `CDE304: TPM device not available`.

## Key Recovery

**There is no automatic recovery mechanism.**

- If TPM fails → data is unrecoverable
- If VM is re-imaged → data is unrecoverable
- If boot chain changes → TPM refuses to unseal

This is by design - keys never leave the VM. See [Security Model](../security.md).

### Customer Options

If backup is needed, customers must:
1. Export LUKS recovery key before TPM enrollment
2. Store recovery key in their own Key Vault
3. Manage recovery themselves
