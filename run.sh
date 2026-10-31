#!/usr/bin/env bash
# Desktop Stat Monitor Launcher
# Supports both pure Wayland and X11/Xwayland backends
# Author: Erek Niemyjski <erek.niemyjski@neuraworksdev.com>
# License: MIT

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

# If user specifies desktop mode or no specific GDK_BACKEND is set,
# use X11 backend if available to allow full desktop pinning & position persistence
if [ -z "$GDK_BACKEND" ]; then
    if [ -n "$DISPLAY" ]; then
        export GDK_BACKEND=x11
    else
        export GDK_BACKEND=wayland
    fi
fi

# Filter arguments
IS_BG=false
FILTERED_ARGS=()
for arg in "$@"; do
    if [ "$arg" = "--bg" ]; then
        IS_BG=true
    else
        FILTERED_ARGS+=("$arg")
    fi
done

# Background daemon mode
if [ "$IS_BG" = true ]; then
    LOG_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/stat_monitor"
    mkdir -p "$LOG_DIR"
    nohup python3 "$SCRIPT_DIR/main.py" "${FILTERED_ARGS[@]}" > "$LOG_DIR/stat-monitor.log" 2>&1 &
    PID=$!
    echo "✓ Stat Monitor started in background [PID: $PID]"
    echo "Logging output to: $LOG_DIR/stat-monitor.log"
    echo "To stop: kill $PID or right-click the overlay and click 'Quit'"
    exit 0
fi

exec python3 "$SCRIPT_DIR/main.py" "${FILTERED_ARGS[@]}"
