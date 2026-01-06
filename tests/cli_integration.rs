//! Integration tests for the CLI binary.
//!
//! These tests verify the CLI interface works correctly by running the
//! actual binary and checking its output.

use assert_cmd::Command;
use predicates::prelude::*;

/// Get a Command for our binary.
#[allow(deprecated)]
fn cde() -> Command {
    Command::cargo_bin("cde").unwrap()
}

#[test]
fn test_dry_run_succeeds() {
    cde()
        .arg("dry-run")
        .assert()
        .success()
        .stdout(predicate::str::contains("Extension invoked"));
}

#[test]
fn test_dry_run_no_args_defaults_to_dry_run() {
    // Running without args should default to dry-run mode
    cde()
        .assert()
        .success()
        .stdout(predicate::str::contains("Extension invoked"));
}

#[test]
fn test_unknown_command_fails() {
    cde()
        .arg("unknown-command")
        .assert()
        .failure()
        .stderr(predicate::str::contains("Unknown command"));
}

#[test]
fn test_help_text_shown_on_unknown_command() {
    cde()
        .arg("invalid")
        .assert()
        .failure()
        .stderr(predicate::str::contains("Usage:"))
        .stderr(predicate::str::contains("install"))
        .stderr(predicate::str::contains("enable"))
        .stderr(predicate::str::contains("disable"));
}

#[test]
fn test_dry_run_logs_disk_discovery() {
    cde()
        .arg("dry-run")
        .assert()
        .success()
        .stdout(predicate::str::contains("Discovered disks"));
}

#[test]
fn test_dry_run_logs_data_disk_identification() {
    cde()
        .arg("dry-run")
        .assert()
        .success()
        .stdout(predicate::str::contains("Identified data disks"));
}

#[test]
fn test_multiple_dry_run_variants_work() {
    // Test various ways to specify dry-run
    for arg in &["dry-run", "dryrun", "--dry-run"] {
        cde().arg(arg).assert().success();
    }
}

#[test]
fn test_dry_run_creates_log_directory() {
    use std::path::Path;

    // Run dry-run which creates ./logs directory
    cde().arg("dry-run").assert().success();

    // Verify logs directory was created
    assert!(Path::new("logs").exists());
}
