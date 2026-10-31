#!/usr/bin/env bash
# Build script for Debian package (.deb) of Desktop Stat Monitor
# Author: Erek Niemyjski <erek.niemyjski@neuraworksdev.com>
# License: MIT
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_NAME="stat-monitor"
VERSION="1.0.0"
ARCH="all"
DEB_NAME="${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
BUILD_DIR="${SCRIPT_DIR}/dist/deb_build"
OUTPUT_DIR="${SCRIPT_DIR}/dist"

echo "Building Debian package: ${DEB_NAME}..."

# Clean old build directory
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}/DEBIAN"
mkdir -p "${BUILD_DIR}/usr/bin"
mkdir -p "${BUILD_DIR}/usr/share/${PACKAGE_NAME}"
mkdir -p "${BUILD_DIR}/usr/share/applications"
mkdir -p "${BUILD_DIR}/usr/share/icons/hicolor/scalable/apps"
mkdir -p "${BUILD_DIR}/usr/share/pixmaps"
mkdir -p "${OUTPUT_DIR}"

# Copy application files
cp "${SCRIPT_DIR}/main.py" "${BUILD_DIR}/usr/share/${PACKAGE_NAME}/"
cp "${SCRIPT_DIR}/ui.py" "${BUILD_DIR}/usr/share/${PACKAGE_NAME}/"
cp "${SCRIPT_DIR}/system_monitor.py" "${BUILD_DIR}/usr/share/${PACKAGE_NAME}/"
cp "${SCRIPT_DIR}/nvme_monitor.py" "${BUILD_DIR}/usr/share/${PACKAGE_NAME}/"
cp "${SCRIPT_DIR}/config_manager.py" "${BUILD_DIR}/usr/share/${PACKAGE_NAME}/"
cp "${SCRIPT_DIR}/style.py" "${BUILD_DIR}/usr/share/${PACKAGE_NAME}/"
cp "${SCRIPT_DIR}/run.sh" "${BUILD_DIR}/usr/share/${PACKAGE_NAME}/"
cp "${SCRIPT_DIR}/stat-monitor.svg" "${BUILD_DIR}/usr/share/${PACKAGE_NAME}/"
cp "${SCRIPT_DIR}/LICENSE" "${BUILD_DIR}/usr/share/${PACKAGE_NAME}/"

# Install application launcher in /usr/bin/stat-monitor
cat << 'EOF' > "${BUILD_DIR}/usr/bin/stat-monitor"
#!/usr/bin/env bash
exec /usr/share/stat-monitor/run.sh "$@"
EOF
chmod 755 "${BUILD_DIR}/usr/bin/stat-monitor"
chmod 755 "${BUILD_DIR}/usr/share/${PACKAGE_NAME}/run.sh"
chmod 755 "${BUILD_DIR}/usr/share/${PACKAGE_NAME}/main.py"

# Icons
cp "${SCRIPT_DIR}/stat-monitor.svg" "${BUILD_DIR}/usr/share/icons/hicolor/scalable/apps/stat-monitor.svg"
cp "${SCRIPT_DIR}/stat-monitor.svg" "${BUILD_DIR}/usr/share/pixmaps/stat-monitor.svg"

# Desktop entry
cat << 'EOF' > "${BUILD_DIR}/usr/share/applications/stat-monitor.desktop"
[Desktop Entry]
Name=Stat Monitor Overlay
Comment=Transparent hardware monitor showing CPU, RAM, and NVMe SSD Life
Exec=/usr/bin/stat-monitor
Icon=stat-monitor
Terminal=false
Type=Application
Categories=System;Monitor;Utility;
Keywords=system;monitor;cpu;ram;nvme;ssd;health;life;overlay;
StartupNotify=false
EOF
chmod 644 "${BUILD_DIR}/usr/share/applications/stat-monitor.desktop"

# Control file with dependencies for apt
cat << EOF > "${BUILD_DIR}/DEBIAN/control"
Package: ${PACKAGE_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Depends: python3, python3-gi, python3-gi-cairo, gir1.2-gtk-3.0, python3-psutil, udisks2
Maintainer: Erek Niemyjski <erek.niemyjski@neuraworksdev.com>
Description: Transparent glassmorphic desktop hardware stat monitor overlay
 A sleek, floating system monitor overlay designed for Linux (GNOME/Wayland/X11).
 Displays live CPU telemetry, RAM usage, and NVMe SSD remaining health & life
 without requiring root or sudo privileges.
EOF
chmod 644 "${BUILD_DIR}/DEBIAN/control"

# Post-installation script
cat << 'EOF' > "${BUILD_DIR}/DEBIAN/postinst"
#!/bin/sh
set -e
if [ -x /usr/bin/update-desktop-database ]; then
    update-desktop-database -q /usr/share/applications || true
fi
if [ -x /usr/bin/gtk-update-icon-cache ]; then
    gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
fi
exit 0
EOF
chmod 755 "${BUILD_DIR}/DEBIAN/postinst"

# Post-removal script
cat << 'EOF' > "${BUILD_DIR}/DEBIAN/postrm"
#!/bin/sh
set -e
if [ -x /usr/bin/update-desktop-database ]; then
    update-desktop-database -q /usr/share/applications || true
fi
if [ -x /usr/bin/gtk-update-icon-cache ]; then
    gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
fi
exit 0
EOF
chmod 755 "${BUILD_DIR}/DEBIAN/postrm"

# Build package
dpkg-deb --build --root-owner-group "${BUILD_DIR}" "${OUTPUT_DIR}/${DEB_NAME}"
ln -sf "${DEB_NAME}" "${OUTPUT_DIR}/${PACKAGE_NAME}.deb"

# Clean temporary build directory
rm -rf "${BUILD_DIR}"

echo "✓ Successfully generated Debian package:"
echo "  -> ${OUTPUT_DIR}/${DEB_NAME}"
echo "  -> ${OUTPUT_DIR}/${PACKAGE_NAME}.deb"
echo ""
echo "To install on any laptop (APT will automatically download and install dependencies):"
echo "  sudo apt install ./${OUTPUT_DIR#${SCRIPT_DIR}/}/${DEB_NAME}"
