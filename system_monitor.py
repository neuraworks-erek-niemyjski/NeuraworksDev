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

    def sample(self):
        """Collect snapshot of CPU, RAM, and system stats."""
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
        }
