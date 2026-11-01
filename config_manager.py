"""
Configuration manager for persisting window positions, modes, opacity, and preferences.

Author: Erek Niemyjski <erek.niemyjski@neuraworksdev.com>
License: MIT
Repository: https://github.com/neuraworks-erek-niemyjski/stat-monitor
"""

import json
import os
import stat
from pathlib import Path

__all__ = ['ConfigManager', 'DEFAULT_CONFIG']


DEFAULT_CONFIG = {
    'window_x': 50,
    'window_y': 50,
    'opacity': 0.75,
    'mode': 'dashboard',  # 'dashboard' or 'compact'
    'on_top': False,       # False: Pin below / desktop level, True: Always on top
    'stick_all_workspaces': True,
    'show_per_core': True,
    'show_disks': True,
    'locked': False,
    'refresh_ms': 1000,
    'theme': 'cyber_slate',
}


class ConfigManager:
    def __init__(self):
        # XDG Base Directory compliant — config stored in ~/.config/stat_monitor/
        self.config_dir = Path.home() / '.config' / 'stat_monitor'
        self.config_file = self.config_dir / 'config.json'
        self.config = dict(DEFAULT_CONFIG)
        self.load()

    def load(self):
        """Load config from disk, validating values against expected types and ranges."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Merge loaded values over defaults so new config keys
                    # are automatically available after upgrades
                    validated = self._validate(loaded)
                    self.config.update(validated)
            except Exception as e:
                print(f"[ConfigManager] Error reading config file: {e}")
        else:
            self.save()

    def save(self):
        """Persist current config to disk with restricted file permissions."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            # Restrict config file to owner-only read/write (0o600)
            os.chmod(self.config_file, stat.S_IRUSR | stat.S_IWUSR)
        except Exception as e:
            print(f"[ConfigManager] Error saving config file: {e}")

    def get(self, key, default=None):
        """Retrieve a config value, falling back to the given default."""
        return self.config.get(key, default)

    def set(self, key, value, autosave=True):
        """Update a config value. autosave=False allows batching multiple
        changes before a single disk write."""
        self.config[key] = value
        if autosave:
            self.save()

    def _validate(self, loaded):
        """Sanitize loaded config values to expected types and ranges."""
        validators = {
            'window_x': lambda v: isinstance(v, (int, float)) and -10000 < v < 10000,
            'window_y': lambda v: isinstance(v, (int, float)) and -10000 < v < 10000,
            'opacity': lambda v: isinstance(v, (int, float)) and 0.0 <= v <= 0.95,
            'mode': lambda v: v in ('dashboard', 'compact'),
            'on_top': lambda v: isinstance(v, bool),
            'locked': lambda v: isinstance(v, bool),
            'show_per_core': lambda v: isinstance(v, bool),
            'show_disks': lambda v: isinstance(v, bool),
            'stick_all_workspaces': lambda v: isinstance(v, bool),
            'refresh_ms': lambda v: isinstance(v, int) and 250 <= v <= 60000,
            'theme': lambda v: isinstance(v, str) and len(v) < 64,
        }
        validated = {}
        for key, value in loaded.items():
            if key in validators:
                if validators[key](value):
                    validated[key] = value
                else:
                    print(f"[ConfigManager] Ignoring invalid config value: {key}={value!r}")
            else:
                validated[key] = value  # Allow unknown keys for forward compatibility
        return validated
