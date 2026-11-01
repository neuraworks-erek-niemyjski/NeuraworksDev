#!/usr/bin/env python3
"""
Desktop Stat Monitor: Transparent glassmorphic hardware overlay for Linux (GNOME/Wayland/X11).
Displays live CPU usage, RAM usage, and NVMe SSD remaining health & life telemetry.

Author: Erek Niemyjski <erek.niemyjski@neuraworksdev.com>
License: MIT
Repository: https://github.com/neuraworks-erek-niemyjski/stat-monitor
"""

__version__ = "1.0.0"

import argparse
import signal

import gi

# GTK 3.0 must be required before any gi.repository imports
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from config_manager import ConfigManager
from nvme_monitor import NVMeMonitor
from system_monitor import SystemMonitor
from ui import StatOverlayWindow


def main():
    parser = argparse.ArgumentParser(
        description="Transparent Desktop Stat Monitor (CPU, RAM, Disks & NVMe SSD Life)"
    )
    parser.add_argument(
        '--version', action='version', version=f'%(prog)s {__version__}'
    )
    parser.add_argument(
        '--compact', action='store_true', help="Launch in compact floating pill bar mode"
    )
    parser.add_argument(
        '--dashboard', action='store_true', help="Launch in full dashboard mode"
    )
    parser.add_argument(
        '--on-top', action='store_true', help="Keep floating always on top (HUD mode)"
    )
    parser.add_argument(
        '--desktop',
        action='store_true',
        help="Pin behind windows onto desktop background (desktop mode)",
    )
    parser.add_argument(
        '--no-disks',
        action='store_true',
        help="Launch with disk partitions section hidden",
    )
    parser.add_argument(
        '--clear',
        action='store_true',
        help="Launch with completely transparent 'Clear Glass' background (opacity 0.0)",
    )
    parser.add_argument(
        '--opacity',
        type=float,
        default=None,
        help="Set window background opacity (0.0 to 0.95)",
    )
    parser.add_argument(
        '--refresh',
        type=int,
        default=None,
        help="Refresh rate in milliseconds (default: 1000ms)",
    )

    args = parser.parse_args()

    # Config manager
    cfg = ConfigManager()

    if args.compact:
        cfg.set('mode', 'compact', autosave=False)
    elif args.dashboard:
        cfg.set('mode', 'dashboard', autosave=False)

    if args.on_top:
        cfg.set('on_top', True, autosave=False)
    elif args.desktop:
        cfg.set('on_top', False, autosave=False)

    if args.no_disks:
        cfg.set('show_disks', False, autosave=False)

    if args.clear:
        cfg.set('opacity', 0.0, autosave=False)
    elif args.opacity is not None:
        cfg.set('opacity', max(0.0, min(0.95, args.opacity)), autosave=False)

    if args.refresh is not None:
        cfg.set('refresh_ms', max(250, args.refresh), autosave=False)

    # Initialize hardware telemetry
    # SystemMonitor wraps psutil; NVMeMonitor queries UDisks2 D-Bus
    sys_mon = SystemMonitor()
    nvme_mon = NVMeMonitor()
    nvme_mon.start_background_loop()

    # Create & display window
    win = StatOverlayWindow(sys_mon, nvme_mon, cfg)
    win.connect('destroy', Gtk.main_quit)
    win.show_all()

    # Handle Ctrl+C in terminal
    def sigint_handler(sig, frame):
        nvme_mon.stop()
        Gtk.main_quit()

    # Also handle SIGTERM for clean shutdown from systemd/process managers
    signal.signal(signal.SIGINT, sigint_handler)
    signal.signal(signal.SIGTERM, sigint_handler)

    # GLib mainloop blocks Python signal handlers; this periodic no-op
    # callback allows them to fire between GTK event processing cycles
    GLib.timeout_add(250, lambda: True)

    try:
        Gtk.main()
    finally:
        nvme_mon.stop()


if __name__ == '__main__':
    main()
