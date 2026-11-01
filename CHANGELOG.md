# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-10-31

### Added
- **Disk Partitions Storage Monitor**:
  - Live monitoring of all active physical and persistent disk partitions (mountpoint, device name, and filesystem type).
  - Used space as a percentage with dynamic warning thresholds (cyan <75%, amber 75%–90%, red >90%).
  - Free space reported directly in gigabytes (GB free) along with used/total capacity.
  - Smooth glowing gradient progress bars for each partition.
  - Intelligent filtering to exclude loopback devices (e.g., Snap packages), ephemeral pseudo-filesystems (`tmpfs`, `devtmpfs`), and container mounts.
  - Scrollable view supporting systems with multiple mounted partitions or external drives.
  - Compact Pill mode integration (`🖴 DISK % (GB free)`) with comprehensive hover tooltip breakdown.
  - Hotkey `D` and right-click context menu toggle to show/hide the Disk Partitions section.
  - CLI argument `--no-disks` to launch with partitions hidden.

## [1.0.0] - 2026-10-31

### Added
- Full dashboard mode with CPU, RAM, and NVMe SSD health monitoring
- Compact floating pill bar mode
- Glassmorphic transparent UI with adjustable opacity (0%–90%)
- Desktop pinning and always-on-top (HUD) modes
- Per-core CPU utilization bars
- NVMe SMART health via UDisks2 D-Bus (no sudo required)
- Keyboard shortcuts for all common actions
- Persistent window position and settings via `~/.config/stat_monitor/config.json`
- Debian package (`.deb`) build script with automatic dependency resolution
- Desktop launcher and autostart support
- Multi-distro installation instructions (Ubuntu, Fedora, Arch)
