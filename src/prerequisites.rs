//! Prerequisite checking for the Confidential Disk Encryption Extension.
//!
//! This module validates that the VM meets all requirements before attempting
//! disk encryption. If prerequisites are not met, it returns detailed error
//! messages that are reported back to Azure.

use crate::error::{Error, ErrorCode, Result};
use std::process::Command;
use tracing::{debug, error, info, warn};

#[cfg(target_os = "linux")]
use std::path::Path;

/// Result of a prerequisite check.
#[derive(Debug, Clone)]
pub struct PrerequisiteCheck {
    /// Name of the check.
    pub name: String,
    /// Whether the check passed.
    pub passed: bool,
    /// Human-readable message describing the result.
    pub message: String,
    /// Severity if the check failed.
    pub severity: CheckSeverity,
}

/// Severity of a failed prerequisite check.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CheckSeverity {
    /// Check failed and extension cannot proceed.
    Error,
    /// Check failed but extension may be able to proceed with reduced functionality.
    Warning,
    /// Informational only.
    Info,
}

impl PrerequisiteCheck {
    fn pass(name: &str, message: &str) -> Self {
        Self {
            name: name.to_string(),
            passed: true,
            message: message.to_string(),
            severity: CheckSeverity::Info,
        }
    }

    fn fail(name: &str, message: &str, severity: CheckSeverity) -> Self {
        Self {
            name: name.to_string(),
            passed: false,
            message: message.to_string(),
            severity,
        }
    }
}

/// Summary of all prerequisite checks.
#[derive(Debug)]
pub struct PrerequisiteReport {
    /// Individual check results.
    pub checks: Vec<PrerequisiteCheck>,
    /// Overall result - true if all required checks passed.
    pub all_passed: bool,
    /// Number of errors.
    pub error_count: usize,
    /// Number of warnings.
    pub warning_count: usize,
}

impl PrerequisiteReport {
    /// Create a report from a list of checks.
    fn from_checks(checks: Vec<PrerequisiteCheck>) -> Self {
        let error_count = checks
            .iter()
            .filter(|c| !c.passed && c.severity == CheckSeverity::Error)
            .count();
        let warning_count = checks
            .iter()
            .filter(|c| !c.passed && c.severity == CheckSeverity::Warning)
            .count();
        let all_passed = error_count == 0;

        Self {
            checks,
            all_passed,
            error_count,
            warning_count,
        }
    }

    /// Convert the report to an error if any checks failed.
    pub fn into_result(self) -> Result<()> {
        if self.all_passed {
            Ok(())
        } else {
            let errors: Vec<String> = self
                .checks
                .iter()
                .filter(|c| !c.passed && c.severity == CheckSeverity::Error)
                .map(|c| format!("{}: {}", c.name, c.message))
                .collect();

            Err(Error::with_message(ErrorCode::PrerequisitesNotMet, errors.join("; ")))
        }
    }
}

/// Prerequisite checker for the extension.
pub struct PrerequisiteChecker;

impl PrerequisiteChecker {
    /// Run all prerequisite checks.
    ///
    /// Returns a report with all check results.
    pub fn run_all_checks() -> PrerequisiteReport {
        info!("Running prerequisite checks");

        let mut checks = Vec::new();

        // Platform-specific checks
        #[cfg(target_os = "linux")]
        {
            checks.push(Self::check_cryptsetup());
            checks.push(Self::check_luks2_support());
            checks.push(Self::check_dm_crypt_module());
            checks.push(Self::check_systemd());
            checks.push(Self::check_tpm_device());
        }

        #[cfg(target_os = "windows")]
        {
            checks.push(Self::check_bitlocker());
            checks.push(Self::check_tpm_windows());
        }

        // Common checks
        checks.push(Self::check_root_permissions());
        checks.push(Self::check_disk_space());

        let report = PrerequisiteReport::from_checks(checks);

        // Log results
        for check in &report.checks {
            if check.passed {
                info!(check = %check.name, "✓ {}", check.message);
            } else {
                match check.severity {
                    CheckSeverity::Error => error!(check = %check.name, "✗ {}", check.message),
                    CheckSeverity::Warning => warn!(check = %check.name, "⚠ {}", check.message),
                    CheckSeverity::Info => debug!(check = %check.name, "ℹ {}", check.message),
                }
            }
        }

        info!(
            passed = report.all_passed,
            errors = report.error_count,
            warnings = report.warning_count,
            "Prerequisite checks complete"
        );

        report
    }

    /// Quick check that returns an error if prerequisites are not met.
    pub fn ensure_prerequisites() -> Result<()> {
        Self::run_all_checks().into_result()
    }

    // =========================================================================
    // Linux Checks
    // =========================================================================

    #[cfg(target_os = "linux")]
    fn check_cryptsetup() -> PrerequisiteCheck {
        let name = "cryptsetup";

        match Command::new("which").arg("cryptsetup").output() {
            Ok(output) if output.status.success() => {
                // Also check version
                match Command::new("cryptsetup").arg("--version").output() {
                    Ok(ver) => {
                        let version = String::from_utf8_lossy(&ver.stdout);
                        PrerequisiteCheck::pass(name, &format!("cryptsetup found: {}", version.trim()))
                    }
                    Err(_) => PrerequisiteCheck::pass(name, "cryptsetup found"),
                }
            }
            _ => PrerequisiteCheck::fail(
                name,
                "cryptsetup not found. Install with: apt install cryptsetup (Debian/Ubuntu) or dnf install cryptsetup (RHEL/Fedora)",
                CheckSeverity::Error,
            ),
        }
    }

    #[cfg(target_os = "linux")]
    fn check_luks2_support() -> PrerequisiteCheck {
        let name = "LUKS2 support";

        // Check if cryptsetup supports LUKS2
        match Command::new("cryptsetup").args(["--help"]).output() {
            Ok(output) => {
                let help_text = String::from_utf8_lossy(&output.stdout);
                if help_text.contains("luks2") || help_text.contains("LUKS2") {
                    PrerequisiteCheck::pass(name, "LUKS2 format supported")
                } else {
                    // LUKS2 is default since cryptsetup 2.1, so this is unlikely
                    PrerequisiteCheck::fail(
                        name,
                        "cryptsetup version may not support LUKS2. Version 2.1+ required.",
                        CheckSeverity::Warning,
                    )
                }
            }
            Err(_) => PrerequisiteCheck::fail(
                name,
                "Could not determine LUKS2 support",
                CheckSeverity::Warning,
            ),
        }
    }

    #[cfg(target_os = "linux")]
    fn check_dm_crypt_module() -> PrerequisiteCheck {
        let name = "dm-crypt kernel module";

        // Check if dm-crypt module is loaded or built-in
        if Path::new("/dev/mapper/control").exists() {
            PrerequisiteCheck::pass(name, "dm-crypt available (/dev/mapper/control exists)")
        } else {
            // Try to load the module
            match Command::new("modprobe").arg("dm-crypt").output() {
                Ok(output) if output.status.success() => {
                    PrerequisiteCheck::pass(name, "dm-crypt module loaded successfully")
                }
                _ => PrerequisiteCheck::fail(
                    name,
                    "dm-crypt kernel module not available. Kernel may need to be rebuilt with CONFIG_DM_CRYPT=y",
                    CheckSeverity::Error,
                ),
            }
        }
    }

    #[cfg(target_os = "linux")]
    fn check_systemd() -> PrerequisiteCheck {
        let name = "systemd";

        match Command::new("systemctl").arg("--version").output() {
            Ok(output) if output.status.success() => {
                let version_str = String::from_utf8_lossy(&output.stdout);
                // Parse version number (e.g., "systemd 252")
                let version = version_str
                    .lines()
                    .next()
                    .and_then(|line| line.split_whitespace().nth(1))
                    .and_then(|v| v.parse::<u32>().ok())
                    .unwrap_or(0);

                if version >= 248 {
                    PrerequisiteCheck::pass(
                        name,
                        &format!("systemd {} found (TPM2 support available)", version),
                    )
                } else {
                    PrerequisiteCheck::fail(
                        name,
                        &format!(
                            "systemd {} found, but version 248+ required for TPM2 auto-unlock. \
                             Encryption will work but auto-unlock may require Key Vault.",
                            version
                        ),
                        CheckSeverity::Warning,
                    )
                }
            }
            _ => PrerequisiteCheck::fail(
                name,
                "systemd not found. TPM-based auto-unlock will not be available.",
                CheckSeverity::Warning,
            ),
        }
    }

    #[cfg(target_os = "linux")]
    fn check_tpm_device() -> PrerequisiteCheck {
        let name = "vTPM device";

        let tpm0_exists = Path::new("/dev/tpm0").exists();
        let tpmrm0_exists = Path::new("/dev/tpmrm0").exists();

        if tpm0_exists || tpmrm0_exists {
            // Also check if systemd-cryptenroll can see it
            match Command::new("systemd-cryptenroll")
                .args(["--tpm2-device=list"])
                .output()
            {
                Ok(output) if output.status.success() => {
                    PrerequisiteCheck::pass(name, "vTPM available and accessible by systemd-cryptenroll")
                }
                _ => PrerequisiteCheck::pass(
                    name,
                    "vTPM device exists but systemd-cryptenroll may not be available",
                )
            }
        } else {
            PrerequisiteCheck::fail(
                name,
                "No vTPM device found (/dev/tpm0 or /dev/tpmrm0). \
                 This VM may not be Trusted Launch or Confidential. \
                 Auto-unlock will fall back to Key Vault.",
                CheckSeverity::Warning,
            )
        }
    }

    // =========================================================================
    // Windows Checks
    // =========================================================================

    #[cfg(target_os = "windows")]
    fn check_bitlocker() -> PrerequisiteCheck {
        let name = "BitLocker";

        match Command::new("where").arg("manage-bde").output() {
            Ok(output) if output.status.success() => {
                PrerequisiteCheck::pass(name, "BitLocker (manage-bde) available")
            }
            _ => PrerequisiteCheck::fail(
                name,
                "BitLocker not available. Enable the BitLocker feature in Windows.",
                CheckSeverity::Error,
            ),
        }
    }

    #[cfg(target_os = "windows")]
    fn check_tpm_windows() -> PrerequisiteCheck {
        let name = "TPM";

        match Command::new("powershell")
            .args(["-Command", "Get-Tpm | Select-Object -ExpandProperty TpmPresent"])
            .output()
        {
            Ok(output) => {
                let result = String::from_utf8_lossy(&output.stdout);
                if result.trim().eq_ignore_ascii_case("true") {
                    PrerequisiteCheck::pass(name, "TPM present and available")
                } else {
                    PrerequisiteCheck::fail(
                        name,
                        "TPM not present or not enabled. BitLocker auto-unlock may not work.",
                        CheckSeverity::Warning,
                    )
                }
            }
            Err(_) => PrerequisiteCheck::fail(
                name,
                "Could not check TPM status",
                CheckSeverity::Warning,
            ),
        }
    }

    // =========================================================================
    // Common Checks
    // =========================================================================

    fn check_root_permissions() -> PrerequisiteCheck {
        let name = "Root/Admin permissions";

        #[cfg(target_os = "linux")]
        {
            if unsafe { libc::geteuid() } == 0 {
                PrerequisiteCheck::pass(name, "Running as root")
            } else {
                PrerequisiteCheck::fail(
                    name,
                    "Not running as root. Disk encryption requires root privileges.",
                    CheckSeverity::Error,
                )
            }
        }

        #[cfg(target_os = "windows")]
        {
            // Check if running as administrator
            match Command::new("net").arg("session").output() {
                Ok(output) if output.status.success() => {
                    PrerequisiteCheck::pass(name, "Running as Administrator")
                }
                _ => PrerequisiteCheck::fail(
                    name,
                    "Not running as Administrator. Disk encryption requires admin privileges.",
                    CheckSeverity::Error,
                ),
            }
        }
    }

    fn check_disk_space() -> PrerequisiteCheck {
        let name = "Disk space";

        // Check if there's enough space in /tmp or temp directory for temporary files
        #[cfg(target_os = "linux")]
        let temp_path = "/tmp";
        #[cfg(target_os = "windows")]
        let temp_path = std::env::temp_dir();

        // For now, just check the path exists
        #[cfg(target_os = "linux")]
        let path = Path::new(temp_path);
        #[cfg(target_os = "windows")]
        let path = temp_path.as_path();

        if path.exists() {
            PrerequisiteCheck::pass(name, "Temporary directory accessible")
        } else {
            PrerequisiteCheck::fail(
                name,
                "Temporary directory not accessible",
                CheckSeverity::Warning,
            )
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_prerequisite_check_pass() {
        let check = PrerequisiteCheck::pass("test", "Test passed");
        assert!(check.passed);
        assert_eq!(check.name, "test");
    }

    #[test]
    fn test_prerequisite_check_fail() {
        let check = PrerequisiteCheck::fail("test", "Test failed", CheckSeverity::Error);
        assert!(!check.passed);
        assert_eq!(check.severity, CheckSeverity::Error);
    }

    #[test]
    fn test_report_all_passed() {
        let checks = vec![
            PrerequisiteCheck::pass("check1", "OK"),
            PrerequisiteCheck::pass("check2", "OK"),
        ];
        let report = PrerequisiteReport::from_checks(checks);
        assert!(report.all_passed);
        assert_eq!(report.error_count, 0);
    }

    #[test]
    fn test_report_has_errors() {
        let checks = vec![
            PrerequisiteCheck::pass("check1", "OK"),
            PrerequisiteCheck::fail("check2", "Failed", CheckSeverity::Error),
        ];
        let report = PrerequisiteReport::from_checks(checks);
        assert!(!report.all_passed);
        assert_eq!(report.error_count, 1);
    }

    #[test]
    fn test_report_warnings_dont_fail() {
        let checks = vec![
            PrerequisiteCheck::pass("check1", "OK"),
            PrerequisiteCheck::fail("check2", "Warning", CheckSeverity::Warning),
        ];
        let report = PrerequisiteReport::from_checks(checks);
        assert!(report.all_passed); // Warnings don't fail the overall check
        assert_eq!(report.warning_count, 1);
    }

    #[test]
    fn test_into_result_success() {
        let checks = vec![PrerequisiteCheck::pass("check1", "OK")];
        let report = PrerequisiteReport::from_checks(checks);
        assert!(report.into_result().is_ok());
    }

    #[test]
    fn test_into_result_failure() {
        let checks = vec![PrerequisiteCheck::fail("check1", "Failed", CheckSeverity::Error)];
        let report = PrerequisiteReport::from_checks(checks);
        assert!(report.into_result().is_err());
    }
}
