use sysinfo::Disks;

fn main() {
    println!("=== Disk Information ===\n");

    let disks = Disks::new_with_refreshed_list();

    if disks.list().is_empty() {
        println!("No disks found on this system.");
        return;
    }

    for disk in disks.list() {
        let total_gb = disk.total_space() as f64 / 1_073_741_824.0;
        let available_gb = disk.available_space() as f64 / 1_073_741_824.0;
        let used_gb = total_gb - available_gb;
        let usage_percent = if total_gb > 0.0 {
            (used_gb / total_gb) * 100.0
        } else {
            0.0
        };

        println!("Disk: {}", disk.name().to_string_lossy());
        println!("  Mount Point:    {}", disk.mount_point().display());
        println!("  File System:    {}", disk.file_system().to_string_lossy());
        println!("  Type:           {:?}", disk.kind());
        println!("  Total Space:    {:.2} GB", total_gb);
        println!("  Available:      {:.2} GB", available_gb);
        println!("  Used:           {:.2} GB ({:.1}%)", used_gb, usage_percent);
        println!("  Removable:      {}", disk.is_removable());
        println!();
    }
}
