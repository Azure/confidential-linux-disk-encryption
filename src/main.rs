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

use confidential_disk_encryption::Error;
use confidential_disk_encryption::{
    handler::ExtensionHandler, logging, ErrorCode, PrerequisiteChecker, Result,
};
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
    /// Check prerequisites without performing encryption
    CheckPrereqs,
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
            "check-prereqs" | "check-prerequisites" | "prereqs" => Some(Command::CheckPrereqs),
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
    eprintln!("  dry-run        Discover disks and show what would be encrypted");
    eprintln!("  check-prereqs  Check if the VM meets all prerequisites");
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
                return Err(Error::with_message(
                    ErrorCode::InvalidConfiguration,
                    format!("Unknown command: {}", args[1]),
                ));
            }
        }
    };

    // Initialize logging
    // Use dev logging for dry-run and check-prereqs (logs to stdout + file in ./logs)
    // Use production logging for other commands (logs to system location)
    let _guard = if command == Command::DryRun || command == Command::CheckPrereqs {
        logging::init_dev_logging()?
    } else {
        logging::init_default_logging()?
    };

    info!(command = ?command, "Extension invoked");

    // Handle check-prereqs specially - it doesn't need a handler
    if command == Command::CheckPrereqs {
        let report = PrerequisiteChecker::run_all_checks();

        // Print summary
        println!();
        println!("=== Prerequisite Check Summary ===");
        println!();
        for check in &report.checks {
            let status = if check.passed { "✓" } else { "✗" };
            println!("  {} {}: {}", status, check.name, check.message);
        }
        println!();

        if report.all_passed {
            println!("All prerequisites met! The extension can run on this VM.");
            return Ok(());
        } else {
            println!(
                "Prerequisites check failed: {} error(s), {} warning(s)",
                report.error_count, report.warning_count
            );
            return report.into_result();
        }
    }

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
        Command::CheckPrereqs => unreachable!(), // Handled above
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
