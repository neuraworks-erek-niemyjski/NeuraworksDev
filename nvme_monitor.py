"""
NVMe SSD SMART & Health Life Monitor using FreeDesktop UDisks2 DBus.
Queries NVMe controller telemetry for remaining life, wear percentage,
spare capacity, total data written/read, and drive temperature.

Author: Erek Niemyjski <erek.niemyjski@neuraworksdev.com>
License: MIT
Repository: https://github.com/neuraworks-erek-niemyjski/stat-monitor

References & Specifications:
- FreeDesktop UDisks2 D-Bus API: org.freedesktop.UDisks2.NVMe.Controller
  https://storaged.org/doc/udisks2-api/latest/gdbus-org.freedesktop.UDisks2.NVMe.Controller.html
- NVM Express™ Base Specification (SMART / Health Information Log):
  https://nvmexpress.org
"""

import threading
import time
import gi

gi.require_version('Gio', '2.0')
from gi.repository import Gio, GLib

__all__ = ['NVMeMonitor']


class NVMeMonitor:
    def __init__(self, refresh_interval=10):
        self.refresh_interval = refresh_interval
        self._lock = threading.Lock()
        self._cached_drives = []
        self._selected_index = 0
        self._bus = None
        self._running = False
        self._thread = None

        self._init_dbus()
        self.refresh()

    def _init_dbus(self):
        try:
            self._bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        except Exception as e:
            print(f"[NVMeMonitor] Warning: Could not connect to system DBus: {e}")
            self._bus = None

    def refresh(self):
        """Query UDisks2 for all NVMe controllers and SMART health data."""
        if not self._bus:
            self._init_dbus()
            if not self._bus:
                return []

        try:
            # Use D-Bus ObjectManager to enumerate all UDisks2-managed
            # block devices and controllers on the system bus
            om = Gio.DBusProxy.new_sync(
                self._bus,
                Gio.DBusProxyFlags.NONE,
                None,
                'org.freedesktop.UDisks2',
                '/org/freedesktop/UDisks2',
                'org.freedesktop.DBus.ObjectManager',
                None,
            )
            objects = om.call_sync(
                'GetManagedObjects', None, Gio.DBusCallFlags.NONE, -1, None
            ).unpack()[0]

            drives = []
            for path, interfaces in objects.items():
                if 'org.freedesktop.UDisks2.NVMe.Controller' in interfaces:
                    ctrl_props = interfaces['org.freedesktop.UDisks2.NVMe.Controller']
                    drive_props = interfaces.get('org.freedesktop.UDisks2.Drive', {})

                    # Query SmartGetAttributes
                    smart = {}
                    try:
                        ctrl_proxy = Gio.DBusProxy.new_sync(
                            self._bus,
                            Gio.DBusProxyFlags.NONE,
                            None,
                            'org.freedesktop.UDisks2',
                            path,
                            'org.freedesktop.UDisks2.NVMe.Controller',
                            None,
                        )
                        # SmartGetAttributes returns NVMe SMART/Health Information
                        # Log data (NVMe spec section 5.14.1.2)
                        smart_res = ctrl_proxy.call_sync(
                            'SmartGetAttributes',
                            GLib.Variant('(a{sv})', ({},)),
                            Gio.DBusCallFlags.NONE,
                            -1,
                            None,
                        )
                        smart = smart_res.unpack()[0]
                    except Exception as ex:
                        # SMART attributes may be unavailable on some NVMe controllers
                        # (e.g., USB-attached NVMe enclosures, or controllers without SMART support)
                        print(f"[NVMeMonitor] SMART query skipped for {path}: {ex}")

                    model = drive_props.get('Model', 'NVMe Solid State Drive')
                    serial = drive_props.get('Serial', '')
                    # percent_used: NVMe wear indicator (0=new, 100=endurance exhausted, can exceed 100)
                    percent_used = int(smart.get('percent_used', 0))
                    avail_spare = int(smart.get('avail_spare', 100))
                    spare_thresh = int(smart.get('spare_thresh', 10))

                    # UDisks2 reports data_written/read in bytes;
                    # convert to terabytes (SI: 1 TB = 10^12 bytes)
                    raw_written = int(smart.get('total_data_written', 0))
                    raw_read = int(smart.get('total_data_read', 0))
                    tb_written = raw_written / (1000**4)
                    tb_read = raw_read / (1000**4)

                    power_on_hours = int(ctrl_props.get('SmartPowerOnHours', 0))

                    # NVMe spec reports temperature in Kelvin; convert to Celsius
                    temp_k = float(ctrl_props.get('SmartTemperature', 0))
                    if temp_k == 0 and 'temp_sensors' in smart and smart['temp_sensors']:
                        temp_k = float(smart['temp_sensors'][0])
                    temp_c = (temp_k - 273.15) if temp_k > 0 else 0.0

                    # Remaining life = 100% minus cumulative wear percentage (clamped to 0)
                    life_left = max(0, 100 - percent_used)

                    # Health tier thresholds loosely based on NVMe endurance
                    # management best practices and spare capacity thresholds
                    if life_left >= 80 and avail_spare >= 80:
                        health_status = 'EXCELLENT'
                        health_color = '#10b981'  # Emerald green
                    elif life_left >= 50:
                        health_status = 'GOOD'
                        health_color = '#06b6d4'  # Cyan
                    elif life_left >= 20:
                        health_status = 'WARNING'
                        health_color = '#f59e0b'  # Amber
                    else:
                        health_status = 'CRITICAL'
                        health_color = '#ef4444'  # Red

                    drives.append({
                        'path': path,
                        'model': model,
                        'serial': serial,
                        'life_left_percent': life_left,
                        'percent_used': percent_used,
                        'avail_spare': avail_spare,
                        'spare_thresh': spare_thresh,
                        'tb_written': round(tb_written, 2),
                        'tb_read': round(tb_read, 2),
                        'power_on_hours': power_on_hours,
                        'temp_c': round(temp_c, 1),
                        'health_status': health_status,
                        'health_color': health_color,
                    })

            with self._lock:
                self._cached_drives = drives
                if self._selected_index >= len(drives):
                    self._selected_index = 0
            return drives

        except Exception as e:
            print(f"[NVMeMonitor] Error querying NVMe drives: {e}")
            return []

    def start_background_loop(self):
        """Starts periodic background updates so UI calls are non-blocking."""
        if self._running:
            return
        self._running = True

        def _worker():
            # Worker sleeps first, then refreshes — avoids double-query on startup
            # since __init__ already calls refresh()
            while self._running:
                time.sleep(self.refresh_interval)
                if not self._running:
                    break
                self.refresh()

        self._thread = threading.Thread(target=_worker, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def get_all_drives(self):
        with self._lock:
            return list(self._cached_drives)

    def get_primary_drive(self):
        with self._lock:
            if self._cached_drives and 0 <= self._selected_index < len(self._cached_drives):
                return self._cached_drives[self._selected_index]
            # Fallback mockup if no NVMe drive detected
            return {
                'path': 'none',
                'model': 'No NVMe Detected',
                'serial': 'N/A',
                'life_left_percent': 100,
                'percent_used': 0,
                'avail_spare': 100,
                'spare_thresh': 10,
                'tb_written': 0.0,
                'tb_read': 0.0,
                'power_on_hours': 0,
                'temp_c': 0.0,
                'health_status': 'UNKNOWN',
                'health_color': '#94a3b8',
            }

    def set_selected_index(self, idx):
        with self._lock:
            if 0 <= idx < len(self._cached_drives):
                self._selected_index = idx
