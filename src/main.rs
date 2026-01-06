//! Confidential Disk Encryption Extension - Entry Point
//!
//! This binary serves as the entry point for the Azure VM extension.
//! It is invoked by the Azure VM agent with commands like:
//! - `install`
//! - `enable`
//! - `disable`
//! - `update`
//! - `uninstall`
//!
//! The extension automatically encrypts all data disks when enabled.

use confidential_disk_encryption::{handler::ExtensionHandler, logging, Result};
use std::env;
use std::process::ExitCode;
use tracing::{error, info};

/// Extension commands that can be invoked by Azure.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Command {
    Install,
    Enable,
    Disable,
    Update,
    Uninstall,
    /// For development: show disk info without encrypting
    DryRun,
}

impl Command {
    fn from_arg(arg: &str) -> Option<Self> {
        match arg.to_lowercase().as_str() {
            "install" => Some(Command::Install),
            "enable" => Some(Command::Enable),
            "disable" => Some(Command::Disable),
            "update" => Some(Command::Update),
            "uninstall" => Some(Command::Uninstall),
            "dry-run" | "dryrun" | "--dry-run" => Some(Command::DryRun),
            _ => None,
        }
    }
}

fn print_usage() {
    eprintln!("Confidential Disk Encryption Extension");
    eprintln!();
    eprintln!("Usage: cde <command>");
    eprintln!();
    eprintln!("Commands (Azure VM extension):");
    eprintln!("  install     Initialize the extension");
    eprintln!("  enable      Encrypt all data disks");
    eprintln!("  disable     Disable the extension (disks remain encrypted)");
    eprintln!("  update      Update the extension");
    eprintln!("  uninstall   Remove the extension (disks remain encrypted)");
    eprintln!();
    eprintln!("Commands (Development):");
    eprintln!("  dry-run     Discover disks and show what would be encrypted");
}

fn run() -> Result<()> {
    // Parse command from arguments
    let args: Vec<String> = env::args().collect();
    
    let command = if args.len() < 2 {
        // Default to dry-run for development convenience
        Command::DryRun
    } else {
        match Command::from_arg(&args[1]) {
            Some(cmd) => cmd,
            None => {
                print_usage();
                return Err(confidential_disk_encryption::Error::InvalidConfiguration(
                    format!("Unknown command: {}", args[1]),
                ));
            }
        }
    };

    // Initialize logging
    // Use dev logging for dry-run (logs to stdout + file in ./logs)
    // Use production logging for other commands (logs to system location)
    let _guard = if command == Command::DryRun {
        logging::init_dev_logging()?
    } else {
        logging::init_default_logging()?
    };

    info!(command = ?command, "Extension invoked");

    // Create handler (dry-run mode for DryRun command)
    let handler = if command == Command::DryRun {
        ExtensionHandler::new_dry_run()
    } else {
        ExtensionHandler::new()
    };

    // Execute the appropriate handler
    match command {
        Command::Install => handler.handle_install(),
        Command::Enable | Command::DryRun => handler.handle_enable(),
        Command::Disable => handler.handle_disable(),
        Command::Update => handler.handle_update(),
        Command::Uninstall => handler.handle_uninstall(),
    }
}

fn main() -> ExitCode {
    match run() {
        Ok(()) => {
            // Success is logged by the handler
            ExitCode::SUCCESS
        }
        Err(e) => {
            // Log error and exit with failure
            // Note: If logging failed to initialize, this will print to stderr
            error!(error = %e, "Extension failed");
            eprintln!("Error: {}", e);
            ExitCode::FAILURE
        }
    }
}
