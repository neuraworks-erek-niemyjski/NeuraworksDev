"""
Transparent Glassmorphic Desktop Stat Monitor UI.
Supports Full Dashboard and Compact Floating Pill modes, dragging,
pin-to-desktop, always-on-top, dynamic opacity, and real-time updates.

Author: Erek Niemyjski <erek.niemyjski@neuraworksdev.com>
License: MIT
Repository: https://github.com/neuraworks-erek-niemyjski/stat-monitor
"""

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('Pango', '1.0')
from gi.repository import Gtk, Gdk, GLib, Pango

from style import generate_css

__all__ = ['StatOverlayWindow']


class StatOverlayWindow(Gtk.Window):
    def __init__(self, system_monitor, nvme_monitor, config_manager):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)

        self.sys_mon = system_monitor
        self.nvme_mon = nvme_monitor
        self.config_mgr = config_manager

        # State
        self.mode = self.config_mgr.get('mode', 'dashboard')
        self.opacity = self.config_mgr.get('opacity', 0.75)
        self.is_locked = self.config_mgr.get('locked', False)
        self.on_top = self.config_mgr.get('on_top', False)
        self.show_per_core = self.config_mgr.get('show_per_core', True)

        self.drag_start_x = 0
        self.drag_start_y = 0
        self.core_bars = []

        # Window properties
        self.set_title("System Stat Overlay")
        self.set_role("stat_monitor_overlay")
        # app_paintable allows drawing custom backgrounds;
        # decorated=False removes the window manager title bar and borders
        self.set_decorated(False)
        self.set_app_paintable(True)
        self.set_resizable(False)

        # Request RGBA visual for true transparency (compositing must be enabled)
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)

        # Style provider
        self.css_provider = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_screen(
            screen, self.css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        self.apply_theme()

        # Window behaviour & hints
        self.apply_window_state()

        # Event masks for mouse dragging & context menu
        self.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.KEY_PRESS_MASK
        )
        self.connect("button-press-event", self.on_button_press)
        self.connect("key-press-event", self.on_key_press)
        self.connect("configure-event", self.on_configure)

        # Root container
        self.root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(self.root_box)

        # Build UI views
        self.dashboard_widget = self.build_dashboard_view()
        self.compact_widget = self.build_compact_view()

        if self.mode == 'compact':
            self.root_box.pack_start(self.compact_widget, True, True, 0)
        else:
            self.root_box.pack_start(self.dashboard_widget, True, True, 0)

        # Position window from config
        init_x = self.config_mgr.get('window_x', 50)
        init_y = self.config_mgr.get('window_y', 50)
        self.move(init_x, init_y)

        # Initial metrics refresh
        self.on_tick()

        # Periodic timer
        refresh_ms = self.config_mgr.get('refresh_ms', 1000)
        self.timer_id = GLib.timeout_add(refresh_ms, self.on_tick)

    def apply_theme(self):
        """Reload dynamic CSS with current opacity."""
        css_data = generate_css(self.opacity).encode('utf-8')
        try:
            self.css_provider.load_from_data(css_data)
        except Exception as e:
            print(f"[UI] CSS load error: {e}")

    def apply_window_state(self):
        """Apply keep_above / keep_below, stick on workspaces, and taskbar hints."""
        if self.config_mgr.get('stick_all_workspaces', True):
            self.stick()
        else:
            self.unstick()

        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)

        if self.on_top:
            self.set_keep_below(False)
            self.set_keep_above(True)
        else:
            self.set_keep_above(False)
            self.set_keep_below(True)

    def on_configure(self, widget, event):
        """Save coordinates when moved."""
        pos = self.get_position()
        if pos and len(pos) == 2:
            x, y = pos
            if x != self.config_mgr.get('window_x') or y != self.config_mgr.get('window_y'):
                self.config_mgr.set('window_x', x, autosave=False)
                self.config_mgr.set('window_y', y, autosave=True)
        return False

    def build_dashboard_view(self):
        """Build the full comprehensive HUD dashboard."""
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        card.get_style_context().add_class('hud-card')

        # --- HEADER ---
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header.get_style_context().add_class('header-box')

        # Left: Pulse & Title
        pulse = Gtk.Label(label="●")
        pulse.get_style_context().add_class('status-pulse')
        header.pack_start(pulse, False, False, 0)

        title = Gtk.Label(label="SYSTEM HUD")
        title.get_style_context().add_class('title-label')
        header.pack_start(title, False, False, 0)

        # Right: Quick action buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)

        # Mode toggle button
        self.btn_toggle_mode = Gtk.Button(label="🗕")
        self.btn_toggle_mode.set_tooltip_text("Switch to Compact Bar Mode (M)")
        self.btn_toggle_mode.get_style_context().add_class('hud-btn')
        self.btn_toggle_mode.connect("clicked", lambda b: self.set_mode('compact'))
        btn_box.pack_start(self.btn_toggle_mode, False, False, 0)

        # Placement toggle button (On Top vs Desktop)
        self.btn_pin = Gtk.Button(label="📌" if self.on_top else "🖵")
        self.btn_pin.set_tooltip_text("Toggle Always-on-Top / Pin to Desktop (P)")
        self.btn_pin.get_style_context().add_class('hud-btn')
        self.btn_pin.connect("clicked", self.toggle_placement)
        btn_box.pack_start(self.btn_pin, False, False, 0)

        # Menu button
        self.btn_menu = Gtk.Button(label="⚙")
        self.btn_menu.set_tooltip_text("Settings & Menu (Right-click anywhere)")
        self.btn_menu.get_style_context().add_class('hud-btn')
        self.btn_menu.connect("clicked", lambda b: self.show_context_menu(None))
        btn_box.pack_start(self.btn_menu, False, False, 0)

        # Close button
        btn_close = Gtk.Button(label="✕")
        btn_close.set_tooltip_text("Close (Esc or Ctrl+Q)")
        btn_close.get_style_context().add_class('hud-btn')
        btn_close.get_style_context().add_class('hud-close')
        btn_close.connect("clicked", lambda b: Gtk.main_quit())
        btn_box.pack_start(btn_close, False, False, 0)

        header.pack_end(btn_box, False, False, 0)
        card.pack_start(header, False, False, 0)

        # --- CPU SECTION ---
        cpu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        cpu_box.get_style_context().add_class('stat-section')

        # Row 1: Name & Big Percent
        cpu_top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        cpu_name = Gtk.Label(label="⚡ CPU")
        cpu_name.get_style_context().add_class('metric-name')
        cpu_top.pack_start(cpu_name, False, False, 0)

        self.cpu_sub_label = Gtk.Label(label="-- GHz • -- °C")
        self.cpu_sub_label.get_style_context().add_class('sub-stat')
        cpu_top.pack_start(self.cpu_sub_label, False, False, 4)

        self.cpu_val_label = Gtk.Label(label="0.0%")
        self.cpu_val_label.get_style_context().add_class('metric-value-cpu')
        cpu_top.pack_end(self.cpu_val_label, False, False, 0)
        cpu_box.pack_start(cpu_top, False, False, 0)

        # Progress bar
        self.cpu_bar = Gtk.ProgressBar()
        self.cpu_bar.get_style_context().add_class('cpu-bar')
        self.cpu_bar.set_fraction(0.0)
        cpu_box.pack_start(self.cpu_bar, False, False, 0)

        # Per-core mini bars container
        self.core_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.build_core_bars(self.core_box)
        cpu_box.pack_start(self.core_box, False, False, 0)
        self.core_box.set_visible(self.show_per_core)

        card.pack_start(cpu_box, False, False, 0)

        # --- RAM SECTION ---
        ram_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        ram_box.get_style_context().add_class('stat-section')

        ram_top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        ram_name = Gtk.Label(label="🧠 RAM")
        ram_name.get_style_context().add_class('metric-name')
        ram_top.pack_start(ram_name, False, False, 0)

        self.ram_sub_label = Gtk.Label(label="-- / -- GB")
        self.ram_sub_label.get_style_context().add_class('sub-stat')
        ram_top.pack_start(self.ram_sub_label, False, False, 4)

        self.ram_val_label = Gtk.Label(label="0.0%")
        self.ram_val_label.get_style_context().add_class('metric-value-ram')
        ram_top.pack_end(self.ram_val_label, False, False, 0)
        ram_box.pack_start(ram_top, False, False, 0)

        self.ram_bar = Gtk.ProgressBar()
        self.ram_bar.get_style_context().add_class('ram-bar')
        self.ram_bar.set_fraction(0.0)
        ram_box.pack_start(self.ram_bar, False, False, 0)

        # Ram sub-details: Available & Swap
        ram_bot = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.ram_avail_label = Gtk.Label(label="Avail: -- GB")
        self.ram_avail_label.get_style_context().add_class('dim-label')
        ram_bot.pack_start(self.ram_avail_label, False, False, 0)

        self.swap_label = Gtk.Label(label="Swap: -- GB")
        self.swap_label.get_style_context().add_class('dim-label')
        ram_bot.pack_end(self.swap_label, False, False, 0)
        ram_box.pack_start(ram_bot, False, False, 0)

        card.pack_start(ram_box, False, False, 0)

        # --- NVMe SSD SECTION ---
        ssd_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        ssd_box.get_style_context().add_class('stat-section')

        # Top: Drive model
        ssd_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        ssd_name = Gtk.Label(label="💾 NVMe SSD")
        ssd_name.get_style_context().add_class('metric-name')
        ssd_header.pack_start(ssd_name, False, False, 0)

        self.ssd_model_label = Gtk.Label(label="Samsung PM9A1")
        self.ssd_model_label.get_style_context().add_class('sub-stat')
        self.ssd_model_label.set_ellipsize(Pango.EllipsizeMode.END)
        ssd_header.pack_start(self.ssd_model_label, True, True, 2)

        self.ssd_health_badge = Gtk.Label(label="EXCELLENT")
        self.ssd_health_badge.get_style_context().add_class('badge-excellent')
        ssd_header.pack_end(self.ssd_health_badge, False, False, 0)
        ssd_box.pack_start(ssd_header, False, False, 0)

        # Middle: Remaining Life readout
        ssd_mid = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        ssd_life_tag = Gtk.Label(label="Remaining Life:")
        ssd_life_tag.get_style_context().add_class('dim-label')
        ssd_mid.pack_start(ssd_life_tag, False, False, 0)

        self.ssd_life_val = Gtk.Label(label="100%")
        self.ssd_life_val.get_style_context().add_class('metric-value-ssd')
        ssd_mid.pack_end(self.ssd_life_val, False, False, 0)
        ssd_box.pack_start(ssd_mid, False, False, 0)

        # Health bar
        self.ssd_bar = Gtk.ProgressBar()
        self.ssd_bar.get_style_context().add_class('ssd-bar-good')
        self.ssd_bar.set_fraction(1.0)
        ssd_box.pack_start(self.ssd_bar, False, False, 0)

        # Detailed NVMe Grid: Written, Read, Temp, Spare
        grid = Gtk.Grid()
        grid.set_column_spacing(16)
        grid.set_row_spacing(3)

        # Col 0: Written
        lbl_w_tag = Gtk.Label(label="Written:")
        lbl_w_tag.get_style_context().add_class('dim-label')
        lbl_w_tag.set_halign(Gtk.Align.START)
        grid.attach(lbl_w_tag, 0, 0, 1, 1)

        self.ssd_written_label = Gtk.Label(label="0.0 TB")
        self.ssd_written_label.get_style_context().add_class('detail-val')
        self.ssd_written_label.set_halign(Gtk.Align.START)
        grid.attach(self.ssd_written_label, 1, 0, 1, 1)

        # Col 1: Read
        lbl_r_tag = Gtk.Label(label="Read:")
        lbl_r_tag.get_style_context().add_class('dim-label')
        lbl_r_tag.set_halign(Gtk.Align.START)
        grid.attach(lbl_r_tag, 2, 0, 1, 1)

        self.ssd_read_label = Gtk.Label(label="0.0 TB")
        self.ssd_read_label.get_style_context().add_class('detail-val')
        self.ssd_read_label.set_halign(Gtk.Align.START)
        grid.attach(self.ssd_read_label, 3, 0, 1, 1)

        # Row 1: Temp & Spare
        lbl_t_tag = Gtk.Label(label="Temp:")
        lbl_t_tag.get_style_context().add_class('dim-label')
        lbl_t_tag.set_halign(Gtk.Align.START)
        grid.attach(lbl_t_tag, 0, 1, 1, 1)

        self.ssd_temp_label = Gtk.Label(label="-- °C")
        self.ssd_temp_label.get_style_context().add_class('detail-val')
        self.ssd_temp_label.set_halign(Gtk.Align.START)
        grid.attach(self.ssd_temp_label, 1, 1, 1, 1)

        lbl_s_tag = Gtk.Label(label="Spare:")
        lbl_s_tag.get_style_context().add_class('dim-label')
        lbl_s_tag.set_halign(Gtk.Align.START)
        grid.attach(lbl_s_tag, 2, 1, 1, 1)

        self.ssd_spare_label = Gtk.Label(label="100%")
        self.ssd_spare_label.get_style_context().add_class('detail-val')
        self.ssd_spare_label.set_halign(Gtk.Align.START)
        grid.attach(self.ssd_spare_label, 3, 1, 1, 1)

        ssd_box.pack_start(grid, False, False, 2)
        card.pack_start(ssd_box, False, False, 0)

        # Set width constraint
        card.set_size_request(310, -1)
        return card

    def build_core_bars(self, container):
        """Construct per-core visual grid."""
        # Clean previous
        for child in container.get_children():
            container.remove(child)
        self.core_bars.clear()

        grid = Gtk.Grid()
        grid.set_column_spacing(4)
        grid.set_row_spacing(3)

        sample = self.sys_mon.sample()
        cores = sample['cpu']['cores']
        num_cores = len(cores)

        # Arrange per-core bars in a grid: 10 columns for 10+ cores, else 4 columns minimum
        cols = 10 if num_cores >= 10 else max(4, num_cores)

        for i in range(num_cores):
            bar = Gtk.ProgressBar()
            bar.get_style_context().add_class('core-bar')
            bar.set_fraction(0.0)
            row = i // cols
            col = i % cols
            grid.attach(bar, col, row, 1, 1)
            self.core_bars.append(bar)

        container.pack_start(grid, False, False, 2)

    def build_compact_view(self):
        """Build the ultra-slim floating pill view."""
        pill = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        pill.get_style_context().add_class('compact-card')

        # Drag handle
        handle = Gtk.Label(label="⠇")
        handle.get_style_context().add_class('dim-label')
        pill.pack_start(handle, False, False, 0)

        # CPU Pill
        cpu_pill = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        cpu_pill.get_style_context().add_class('compact-pill')
        lbl_c = Gtk.Label(label="⚡ CPU")
        lbl_c.get_style_context().add_class('compact-label')
        cpu_pill.pack_start(lbl_c, False, False, 0)
        self.compact_cpu_val = Gtk.Label(label="0%")
        self.compact_cpu_val.get_style_context().add_class('compact-val')
        self.compact_cpu_val.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.22, 0.74, 0.97, 1.0))
        cpu_pill.pack_start(self.compact_cpu_val, False, False, 0)
        pill.pack_start(cpu_pill, False, False, 0)

        # RAM Pill
        ram_pill = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        ram_pill.get_style_context().add_class('compact-pill')
        lbl_r = Gtk.Label(label="🧠 RAM")
        lbl_r.get_style_context().add_class('compact-label')
        ram_pill.pack_start(lbl_r, False, False, 0)
        self.compact_ram_val = Gtk.Label(label="0%")
        self.compact_ram_val.get_style_context().add_class('compact-val')
        self.compact_ram_val.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.22, 0.74, 0.97, 1.0))
        ram_pill.pack_start(self.compact_ram_val, False, False, 0)
        pill.pack_start(ram_pill, False, False, 0)

        # NVMe Pill
        ssd_pill = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        ssd_pill.get_style_context().add_class('compact-pill')
        lbl_s = Gtk.Label(label="💾 SSD")
        lbl_s.get_style_context().add_class('compact-label')
        ssd_pill.pack_start(lbl_s, False, False, 0)
        self.compact_ssd_val = Gtk.Label(label="100%")
        self.compact_ssd_val.get_style_context().add_class('compact-val')
        self.compact_ssd_val.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.22, 0.74, 0.97, 1.0))
        ssd_pill.pack_start(self.compact_ssd_val, False, False, 0)
        pill.pack_start(ssd_pill, False, False, 0)

        # Expand button
        btn_expand = Gtk.Button(label="⤢")
        btn_expand.set_tooltip_text("Expand to Full Dashboard (M)")
        btn_expand.get_style_context().add_class('hud-btn')
        btn_expand.connect("clicked", lambda b: self.set_mode('dashboard'))
        pill.pack_start(btn_expand, False, False, 0)

        # Close
        btn_c = Gtk.Button(label="✕")
        btn_c.get_style_context().add_class('hud-btn')
        btn_c.get_style_context().add_class('hud-close')
        btn_c.connect("clicked", lambda b: Gtk.main_quit())
        pill.pack_start(btn_c, False, False, 0)

        return pill

    def set_mode(self, new_mode):
        """Switch between dashboard and compact views."""
        if new_mode == self.mode:
            return
        self.mode = new_mode
        self.config_mgr.set('mode', self.mode)

        # Swap widgets in root box
        for child in self.root_box.get_children():
            self.root_box.remove(child)

        if self.mode == 'compact':
            self.root_box.pack_start(self.compact_widget, True, True, 0)
        else:
            self.root_box.pack_start(self.dashboard_widget, True, True, 0)

        self.root_box.show_all()
        # Resize to (1,1) forces GTK to recalculate natural size for the new content
        self.resize(1, 1)

    def toggle_placement(self, widget=None):
        """Toggle between Always on Top (HUD) and Pin to Desktop."""
        self.on_top = not self.on_top
        self.config_mgr.set('on_top', self.on_top)
        self.apply_window_state()
        if hasattr(self, 'btn_pin'):
            self.btn_pin.set_label("📌" if self.on_top else "🖵")

    def set_opacity(self, op):
        """Adjust background translucency."""
        self.opacity = op
        self.config_mgr.set('opacity', op)
        self.apply_theme()

    def on_tick(self):
        """Main periodic refresh callback."""
        try:
            sys_data = self.sys_mon.sample()
            ssd_data = self.nvme_mon.get_primary_drive()

            # --- Update CPU ---
            cpu = sys_data['cpu']
            cpu_pct = cpu['percent']
            cpu_ghz = cpu['ghz']
            cpu_temp = cpu['temp_c']

            self.cpu_val_label.set_text(f"{cpu_pct:.1f}%")
            self.cpu_bar.set_fraction(min(1.0, cpu_pct / 100.0))

            temp_str = f"{cpu_temp:.0f}°C" if cpu_temp is not None else "--°C"
            self.cpu_sub_label.set_text(f"{cpu_ghz:.2f} GHz • {temp_str}")

            # Update per-core bars only if visible and data is available
            if self.show_per_core and self.core_bars and 'cores' in cpu:
                for idx, c_pct in enumerate(cpu['cores']):
                    if idx < len(self.core_bars):
                        self.core_bars[idx].set_fraction(min(1.0, c_pct / 100.0))

            # --- Update RAM ---
            ram = sys_data['ram']
            ram_pct = ram['percent']
            ram_used = ram['used_gb']
            ram_total = ram['total_gb']
            ram_avail = ram['avail_gb']

            self.ram_val_label.set_text(f"{ram_pct:.1f}%")
            self.ram_bar.set_fraction(min(1.0, ram_pct / 100.0))
            self.ram_sub_label.set_text(f"{ram_used:.1f} / {ram_total:.1f} GB")
            self.ram_avail_label.set_text(f"Avail: {ram_avail:.1f} GB")

            swap = sys_data['swap']
            self.swap_label.set_text(f"Swap: {swap['used_gb']:.1f}/{swap['total_gb']:.1f} GB")

            # --- Update NVMe ---
            life_left = ssd_data.get('life_left_percent', 100)
            model = ssd_data.get('model', 'NVMe SSD')
            written = ssd_data.get('tb_written', 0.0)
            read = ssd_data.get('tb_read', 0.0)
            temp = ssd_data.get('temp_c', 0.0)
            spare = ssd_data.get('avail_spare', 100)
            status = ssd_data.get('health_status', 'EXCELLENT')

            self.ssd_model_label.set_text(model)
            self.ssd_life_val.set_text(f"{life_left}%")
            self.ssd_bar.set_fraction(min(1.0, life_left / 100.0))

            # Cycle through health badge CSS classes — remove all first, then apply matching
            b_ctx = self.ssd_health_badge.get_style_context()
            for cls in ['badge-excellent', 'badge-good', 'badge-warn', 'badge-crit']:
                b_ctx.remove_class(cls)
            if status == 'EXCELLENT':
                b_ctx.add_class('badge-excellent')
            elif status == 'GOOD':
                b_ctx.add_class('badge-good')
            elif status == 'WARNING':
                b_ctx.add_class('badge-warn')
            else:
                b_ctx.add_class('badge-crit')
            self.ssd_health_badge.set_text(status)

            # Details
            self.ssd_written_label.set_text(f"{written:.2f} TB")
            self.ssd_read_label.set_text(f"{read:.2f} TB")
            self.ssd_temp_label.set_text(f"{temp:.0f}°C")
            self.ssd_spare_label.set_text(f"{spare}%")

            # --- Update Compact Pill ---
            self.compact_cpu_val.set_text(f"{cpu_pct:.0f}% ({temp_str})")
            self.compact_ram_val.set_text(f"{ram_pct:.0f}% ({ram_used:.1f}G)")
            self.compact_ssd_val.set_text(f"{life_left}% ({temp:.0f}°C)")

        except Exception as e:
            print(f"[UI] Tick update error: {e}")

        return True  # Keep GLib timer active

    def on_button_press(self, widget, event):
        """Handle dragging and context menu."""
        # Left-click initiates window drag (unless position is locked);
        # right-click opens the context settings menu
        if event.button == 1:  # Left click
            if not self.is_locked:
                self.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)
            return True
        elif event.button == 3:  # Right click
            self.show_context_menu(event)
            return True
        return False

    def on_key_press(self, widget, event):
        """Keyboard shortcuts."""
        keyval = event.keyval
        # Escape or Q
        if keyval in [Gdk.KEY_Escape, Gdk.KEY_q, Gdk.KEY_Q]:
            Gtk.main_quit()
            return True
        # M or Tab: Mode toggle
        elif keyval in [Gdk.KEY_m, Gdk.KEY_M, Gdk.KEY_Tab]:
            self.set_mode('compact' if self.mode == 'dashboard' else 'dashboard')
            return True
        # P: Placement toggle
        elif keyval in [Gdk.KEY_p, Gdk.KEY_P]:
            self.toggle_placement()
            return True
        # L: Lock toggle
        elif keyval in [Gdk.KEY_l, Gdk.KEY_L]:
            self.is_locked = not self.is_locked
            self.config_mgr.set('locked', self.is_locked)
            return True
        # Number keys map to opacity presets:
        # 0=Clear Glass, 1=Ghost, 2=Aero Glass, 3=Dark Glass, 4=Solid
        elif keyval in [Gdk.KEY_0, Gdk.KEY_KP_0, Gdk.KEY_grave]:
            self.set_opacity(0.0)
        elif keyval in [Gdk.KEY_1, Gdk.KEY_KP_1]:
            self.set_opacity(0.20)
        elif keyval in [Gdk.KEY_2, Gdk.KEY_KP_2]:
            self.set_opacity(0.50)
        elif keyval in [Gdk.KEY_3, Gdk.KEY_KP_3]:
            self.set_opacity(0.75)
        elif keyval in [Gdk.KEY_4, Gdk.KEY_KP_4]:
            self.set_opacity(0.90)
        return False

    def show_context_menu(self, event):
        """Display options popup menu."""
        menu = Gtk.Menu()

        # View Mode
        mode_menu_item = Gtk.MenuItem(label=f"Mode: {'Compact Pill' if self.mode == 'dashboard' else 'Full Dashboard'}")
        mode_menu_item.connect("activate", lambda m: self.set_mode('compact' if self.mode == 'dashboard' else 'dashboard'))
        menu.append(mode_menu_item)

        # Placement
        placement_item = Gtk.MenuItem(label=f"Placement: {'Pin to Desktop' if self.on_top else 'Float on Top (HUD)'}")
        placement_item.connect("activate", lambda m: self.toggle_placement())
        menu.append(placement_item)

        # Per-core toggle
        core_toggle = Gtk.CheckMenuItem(label="Show Per-Core CPU Bars")
        core_toggle.set_active(self.show_per_core)
        def _toggle_cores(item):
            self.show_per_core = item.get_active()
            self.config_mgr.set('show_per_core', self.show_per_core)
            self.core_box.set_visible(self.show_per_core)
            self.resize(1, 1)
        core_toggle.connect("toggled", _toggle_cores)
        menu.append(core_toggle)

        # Lock position
        lock_toggle = Gtk.CheckMenuItem(label="Lock Position (Prevent Drag)")
        lock_toggle.set_active(self.is_locked)
        def _toggle_lock(item):
            self.is_locked = item.get_active()
            self.config_mgr.set('locked', self.is_locked)
        lock_toggle.connect("toggled", _toggle_lock)
        menu.append(lock_toggle)

        menu.append(Gtk.SeparatorMenuItem())

        # Opacity Submenu
        op_menu_item = Gtk.MenuItem(label="Window Translucency")
        op_submenu = Gtk.Menu()
        op_menu_item.set_submenu(op_submenu)

        for label, val in [
            ("Clear Glass (0% - Completely Transparent)", 0.0),
            ("Ghost (20%)", 0.20),
            ("Aero Glass (50%)", 0.50),
            ("Dark Glass (75%)", 0.75),
            ("High Contrast (90%)", 0.90),
        ]:
            item = Gtk.MenuItem(label=label)
            item.connect("activate", lambda _, v=val: self.set_opacity(v))
            op_submenu.append(item)
        menu.append(op_menu_item)

        # NVMe Drives Submenu
        drives = self.nvme_mon.get_all_drives()
        if len(drives) > 1:
            drive_menu_item = Gtk.MenuItem(label="Select NVMe Drive")
            drive_submenu = Gtk.Menu()
            drive_menu_item.set_submenu(drive_submenu)
            for idx, d in enumerate(drives):
                item = Gtk.MenuItem(label=f"{d['model']} ({d['life_left_percent']}%)")
                item.connect("activate", lambda _, i=idx: self.nvme_mon.set_selected_index(i))
                drive_submenu.append(item)
            menu.append(drive_menu_item)

        # Reset position
        reset_item = Gtk.MenuItem(label="Reset Position to Top-Left")
        reset_item.connect("activate", lambda m: self.move(50, 50))
        menu.append(reset_item)

        menu.append(Gtk.SeparatorMenuItem())

        # Quit
        quit_item = Gtk.MenuItem(label="Quit Stat Monitor")
        quit_item.connect("activate", lambda m: Gtk.main_quit())
        menu.append(quit_item)

        menu.show_all()
        if event:
            menu.popup(None, None, None, None, event.button, event.time)
        else:
            menu.popup(None, None, None, None, 0, Gtk.get_current_event_time())
