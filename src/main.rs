//! Confidential Disk Encryption Extension CLI
//!
//! This is the command-line entry point for the Confidential Disk Encryption Extension.

use confidential_disk_encryption::disk;

fn main() {
    println!("=== Confidential Disk Encryption Extension ===");
    println!("=== Disk Information ===\n");

    let disks = disk::discover_disks();
    disk::print_disk_info(&disks);
}
