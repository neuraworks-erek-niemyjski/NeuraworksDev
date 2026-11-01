"""
System Hardware Monitor for CPU & RAM usage, temperatures, frequencies, and swap.
Powered by psutil (Giampaolo Rodola & contributors, BSD-3-Clause).

Author: Erek Niemyjski <erek.niemyjski@neuraworksdev.com>
License: MIT
Repository: https://github.com/neuraworks-erek-niemyjski/stat-monitor
"""

from collections import deque
import psutil

__all__ = ['SystemMonitor']


class SystemMonitor:
    def __init__(self, history_len=30):
        self.history_len = history_len
        self.cpu_history = deque([0.0] * history_len, maxlen=history_len)
        self.ram_history = deque([0.0] * history_len, maxlen=history_len)

        # Prime psutil's internal counters — first call returns 0.0,
        # subsequent calls return deltas since the previous call
        psutil.cpu_percent(interval=None)
        psutil.cpu_percent(interval=None, percpu=True)

    def get_cpu_temp(self):
        """Retrieve CPU package/core temperature safely across hardware drivers."""
        temps = getattr(psutil, 'sensors_temperatures', lambda: {})()
        if not temps:
            return None

        # Priority-ordered thermal zone drivers for common Intel/AMD/ARM platforms
        for driver in ['coretemp', 'k10temp', 'zenpower', 'cpu_thermal', 'dell_ddv', 'dell_smm']:
            if driver in temps and temps[driver]:
                for entry in temps[driver]:
                    label = entry.label.lower()
                    if (
                        'package' in label
                        or 'tdie' in label
                        or 'cpu' in label
                        or label == ''
                    ):
                        if entry.current and entry.current > 0:
                            return round(entry.current, 1)
                # Fallback to first non-zero reading in driver
                for entry in temps[driver]:
                    if entry.current and entry.current > 0:
                        return round(entry.current, 1)

        # Generic search
        for _, entries in temps.items():
            for entry in entries:
                label = entry.label.lower()
                if 'cpu' in label or 'package' in label:
                    if entry.current and entry.current > 0:
                        return round(entry.current, 1)
        return None

    def get_disk_partitions(self):
        """
        Enumerate all active physical and persistent disk partitions with
        usage percentage, GB used, GB free, and total capacity.
        Filters out loopback devices (e.g. Snaps), pseudo filesystems,
        and container bind mounts.
        """
        partitions = []
        seen_mountpoints = set()

        ignored_fstypes = {
            'squashfs', 'iso9660', 'nullfs', 'ramfs', 'devtmpfs',
            'tmpfs', 'overlay', 'aufs', 'efivarfs', 'none'
        }
        ignored_prefixes = (
            '/snap', '/var/lib/docker', '/var/lib/containers',
            '/run/user', '/run/credentials'
        )

        try:
            raw_partitions = psutil.disk_partitions(all=False)
        except Exception as e:
            print(f"[SystemMonitor] Warning: Could not enumerate disk partitions: {e}")
            return []

        for part in raw_partitions:
            # Skip loopback devices (e.g., Snap packages)
            if part.device.startswith(('/dev/loop', 'loop')):
                continue

            # Skip virtual / memory / overlay filesystems
            if part.fstype in ignored_fstypes:
                continue

            # Skip container, snap, or ephemeral user mounts
            if part.mountpoint.startswith(ignored_prefixes):
                continue

            if part.mountpoint in seen_mountpoints:
                continue

            try:
                usage = psutil.disk_usage(part.mountpoint)
            except (PermissionError, FileNotFoundError, OSError):
                continue

            # Exclude special zero-size filesystems
            if usage.total == 0:
                continue

            seen_mountpoints.add(part.mountpoint)

            # Device short name (e.g., 'nvme0n1p2' from '/dev/nvme0n1p2')
            device_short = part.device.split('/')[-1] if '/' in part.device else part.device

            # Format GB free and used using binary prefix (1 GiB = 1024^3 bytes)
            total_gb = round(usage.total / (1024**3), 2)
            used_gb = round(usage.used / (1024**3), 2)
            free_gb = round(usage.free / (1024**3), 2)
            percent = round(usage.percent, 1)

            partitions.append({
                'device': part.device,
                'device_short': device_short,
                'mountpoint': part.mountpoint,
                'fstype': part.fstype,
                'total_gb': total_gb,
                'used_gb': used_gb,
                'free_gb': free_gb,
                'percent': percent,
            })

        # Sort partitions: root '/' first, then alphabetical by mountpoint
        partitions.sort(key=lambda x: (0 if x['mountpoint'] == '/' else 1, x['mountpoint']))
        return partitions

    def sample(self):
        """Collect snapshot of CPU, RAM, swap, and disk partition stats."""
        # CPU
        cpu_total = psutil.cpu_percent(interval=None)
        cpu_cores = psutil.cpu_percent(interval=None, percpu=True)
        self.cpu_history.append(cpu_total)

        # Frequency
        freq = psutil.cpu_freq()
        # psutil returns frequency in MHz; convert to GHz for display
        cpu_ghz = round(freq.current / 1000.0, 2) if freq else 0.0

        # CPU Temp
        cpu_temp = self.get_cpu_temp()

        # RAM
        vm = psutil.virtual_memory()
        ram_percent = vm.percent
        # Convert bytes to gibibytes (GiB) using binary prefix (1 GiB = 1024^3 bytes)
        ram_used_gb = round(vm.used / (1024**3), 2)
        ram_total_gb = round(vm.total / (1024**3), 2)
        ram_avail_gb = round(vm.available / (1024**3), 2)
        self.ram_history.append(ram_percent)

        # Swap
        swap = psutil.swap_memory()
        swap_percent = swap.percent
        swap_used_gb = round(swap.used / (1024**3), 2)
        swap_total_gb = round(swap.total / (1024**3), 2)

        # Disk Partitions
        disks = self.get_disk_partitions()

        return {
            'cpu': {
                'percent': cpu_total,
                'cores': cpu_cores,
                'ghz': cpu_ghz,
                'temp_c': cpu_temp,
                'history': list(self.cpu_history),
            },
            'ram': {
                'percent': ram_percent,
                'used_gb': ram_used_gb,
                'total_gb': ram_total_gb,
                'avail_gb': ram_avail_gb,
                'history': list(self.ram_history),
            },
            'swap': {
                'percent': swap_percent,
                'used_gb': swap_used_gb,
                'total_gb': swap_total_gb,
            },
            'disks': disks,
        }
