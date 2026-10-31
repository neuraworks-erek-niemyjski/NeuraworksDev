# Contributing to Desktop Stat Monitor

Thank you for your interest in contributing! Here's how to get started.

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/neuraworks-erek-niemyjski/stat-monitor.git
   cd stat-monitor
   ```

2. Install system dependencies:
   ```bash
   # Ubuntu/Debian
   sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 python3-psutil udisks2

   # Fedora
   sudo dnf install python3-gobject gtk3 python3-psutil udisks2

   # Arch Linux
   sudo pacman -S python-gobject gtk3 python-psutil udisks2
   ```

3. Run the application:
   ```bash
   ./run.sh
   ```

## How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Code Style

- Follow PEP 8 for Python code
- Use descriptive variable names
- Add docstrings to all public methods
- Include comments for non-obvious logic

## Reporting Bugs

Please open an issue with:
- Your Linux distribution and version
- Desktop environment (GNOME, KDE, etc.)
- Display server (Wayland or X11)
- Steps to reproduce the bug
- Any error output from running in foreground mode (`./run.sh`)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
