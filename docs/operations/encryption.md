# Disk Encryption

## Linux (LUKS2)

### Prerequisites
- `cryptsetup` 2.1+
- `dm-crypt` kernel module
- Root permissions

### Process
```bash
# 1. Create LUKS2 container
cryptsetup luksFormat --type luks2 /dev/sdb

# 2. Open container
cryptsetup open /dev/sdb encrypted_disk

# 3. Create filesystem
mkfs.ext4 /dev/mapper/encrypted_disk

# 4. Mount
mount /dev/mapper/encrypted_disk /mnt/data
```

### Check Status
```bash
cryptsetup status encrypted_disk
cryptsetup luksDump /dev/sdb
```

## Windows (BitLocker)

### Prerequisites
- BitLocker feature enabled
- Administrator permissions
- TPM (for auto-unlock)

### Process
```powershell
# 1. Enable BitLocker
Enable-BitLocker -MountPoint "D:" -EncryptionMethod XtsAes256 -UsedSpaceOnly

# 2. Add TPM protector (auto-unlock)
Add-BitLockerKeyProtector -MountPoint "D:" -TpmProtector
```

### Check Status
```powershell
manage-bde -status D:
Get-BitLockerVolume -MountPoint "D:"
```

## Extension Behavior

1. Discover all attached disks
2. Filter to data disks (exclude OS, boot, removable)
3. For each disk:
   - Skip if already encrypted
   - Generate random encryption key
   - Encrypt with LUKS2/BitLocker
   - Set up auto-unlock (see [boot-unlock.md](boot-unlock.md))
