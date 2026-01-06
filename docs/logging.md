# Logging

The extension uses the `tracing` crate for structured logging.

## Log Locations

| Platform | Path |
|----------|------|
| Linux | `/var/log/azure/confidential-disk-encryption/extension.log` |
| Windows | `C:\WindowsAzure\Logs\Plugins\ConfidentialDiskEncryption\extension.log` |
| Development | `./logs/extension.log` |

## Log Levels

| Level | Use |
|-------|-----|
| `error` | Operation failures, unrecoverable errors |
| `warn` | Recoverable issues, missing optional features |
| `info` | Key operations, lifecycle events |
| `debug` | Detailed execution flow (dev only) |
| `trace` | Very verbose (dev only) |

Set via `RUST_LOG` environment variable:
```bash
RUST_LOG=debug cargo run -- dry-run
```

## Log Format

```
2026-01-06T01:56:23.277Z INFO confidential_disk_encryption::handler: Enabling extension
2026-01-06T01:56:23.278Z INFO confidential_disk_encryption::handler: Discovered disks disk_count=3
```

## Configuration

```rust
use confidential_disk_encryption::logging::{init_logging, LogConfig};

let config = LogConfig {
    log_dir: PathBuf::from("/var/log/azure/cde"),
    log_file: "extension.log".to_string(),
    log_level: "info".to_string(),
    log_to_stdout: false,
};

let _guard = init_logging(&config)?;
// Keep _guard alive for the program duration
```

## Development Mode

```rust
// Logs to stdout + ./logs/extension.log at debug level
let _guard = logging::init_dev_logging()?;
```

## Adding Logs

```rust
use tracing::{info, warn, error, debug, instrument};

// Simple log
info!("Extension started");

// With fields
info!(disk_count = 3, "Discovered disks");

// Instrument a function (automatic span)
#[instrument(skip(self), name = "enable")]
fn handle_enable(&self) -> Result<()> {
    info!("Enabling encryption");
    // ...
}
