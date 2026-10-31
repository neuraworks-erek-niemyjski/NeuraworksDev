#!/usr/bin/env bash
# Installs desktop launcher and optional autostart entry
# Author: Erek Niemyjski <erek.niemyjski@neuraworksdev.com>
# License: MIT

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$HOME/.local/share/applications"
AUTOSTART_DIR="$HOME/.config/autostart"

mkdir -p "$APP_DIR"
sed -e "s|^Exec=.*|Exec=$SCRIPT_DIR/run.sh|" \
    -e "s|^Icon=.*|Icon=$SCRIPT_DIR/stat-monitor.svg|" \
    "$SCRIPT_DIR/stat-monitor.desktop" > "$APP_DIR/stat-monitor.desktop"
chmod +x "$APP_DIR/stat-monitor.desktop"
update-desktop-database "$APP_DIR" 2>/dev/null || true

echo "✓ Desktop launcher installed to: $APP_DIR/stat-monitor.desktop"
echo "You can now search and launch 'Stat Monitor Overlay' from your GNOME Applications menu!"

if [[ "$1" == "--autostart" ]]; then
    mkdir -p "$AUTOSTART_DIR"
    cp "$APP_DIR/stat-monitor.desktop" "$AUTOSTART_DIR/"
    echo "✓ Autostart enabled: Will launch on system login ($AUTOSTART_DIR/stat-monitor.desktop)"
fi
