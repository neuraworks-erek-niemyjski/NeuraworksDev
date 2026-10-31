# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
