"""
CSS Theme and Styling Generator for the Transparent Desktop Stat Monitor.
Provides glassmorphic translucency, glowing progress bars, and high-contrast typography.

Author: Erek Niemyjski <erek.niemyjski@neuraworksdev.com>
License: MIT
Repository: https://github.com/neuraworks-erek-niemyjski/stat-monitor
"""

__all__ = ['generate_css']

def generate_css(opacity=0.75):
    """
    Generate CSS dynamically with the requested background opacity.
    Opacity ranges from 0.0 (Clear Glass - completely transparent) to 0.95 (nearly opaque).
    """
    # Clamp opacity to safe range — GTK may render incorrectly at exactly 1.0
    opacity = max(0.0, min(0.95, float(opacity)))

    if opacity <= 0.001:
        # Clear Glass mode: fully transparent background with minimal
        # border for mouse interaction area detection
        card_bg = "transparent"
        section_bg = "transparent"
        section_hover_bg = "rgba(255, 255, 255, 0.05)"
        pill_bg = "transparent"
        border_alpha = 0.10
        card_shadow = "none"
        compact_shadow = "none"
    else:
        # Compute derived alpha values — inner sections are slightly
        # more opaque than the card for visual depth/layering
        border_alpha = min(0.35, opacity * 0.3 + 0.05)
        inner_alpha = min(0.60, opacity * 0.55 + 0.1)
        card_bg = f"rgba(15, 23, 42, {opacity:.2f})"
        section_bg = f"rgba(30, 41, 59, {inner_alpha:.2f})"
        section_hover_bg = f"rgba(30, 41, 59, {inner_alpha + 0.08:.2f})"
        pill_bg = f"rgba(30, 41, 59, {inner_alpha:.2f})"
        card_shadow = "0 16px 40px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(255, 255, 255, 0.05)"
        compact_shadow = "0 12px 30px rgba(0, 0, 0, 0.65)"

    return f"""
    /* Transparent Base Window */
    window {{
        background-color: transparent;
    }}

    /* Main Glass Container - Full Dashboard */
    .hud-card {{
        background-color: {card_bg};
        border: 1px solid rgba(255, 255, 255, {border_alpha:.2f});
        border-radius: 20px;
        padding: 16px 18px;
        box-shadow: {card_shadow};
    }}

    /* Compact Floating Pill Mode */
    .compact-card {{
        background-color: {card_bg};
        border: 1px solid rgba(255, 255, 255, {border_alpha:.2f});
        border-radius: 30px;
        padding: 8px 16px;
        box-shadow: {compact_shadow};
    }}

    /* Elevated Inner Section */
    .stat-section {{
        background-color: {section_bg};
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 12px 14px;
        margin-bottom: 4px;
    }}

    .stat-section:hover {{
        background-color: {section_hover_bg};
        border-color: rgba(255, 255, 255, 0.14);
    }}

    /* Header Bar */
    .header-box {{
        padding-bottom: 8px;
        margin-bottom: 2px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }}

    .title-label {{
        color: #94a3b8;
        font-size: 11px;
        font-weight: 800;
    }}

    .status-pulse {{
        color: #10b981;
        font-size: 13px;
    }}

    /* Micro Action Buttons */
    button.hud-btn {{
        background-color: rgba(255, 255, 255, 0.07);
        border: 1px solid rgba(255, 255, 255, 0.10);
        border-radius: 7px;
        color: #94a3b8;
        padding: 3px 7px;
        font-size: 11px;
        min-width: 24px;
        min-height: 24px;
    }}

    button.hud-btn:hover {{
        background-color: rgba(255, 255, 255, 0.18);
        color: #f8fafc;
        border-color: rgba(255, 255, 255, 0.25);
    }}

    button.hud-close:hover {{
        background-color: rgba(239, 68, 68, 0.5);
        color: #ffffff;
        border-color: #ef4444;
    }}

    /* Metric Labels */
    .metric-name {{
        color: #cbd5e1;
        font-size: 13px;
        font-weight: 700;
    }}

    .metric-value-cpu {{
        color: #38bdf8;
        font-size: 22px;
        font-weight: 900;
        font-family: monospace, sans-serif;
    }}

    .metric-value-ram {{
        color: #38bdf8;
        font-size: 22px;
        font-weight: 900;
        font-family: monospace, sans-serif;
    }}

    .metric-value-ssd {{
        color: #38bdf8;
        font-size: 22px;
        font-weight: 900;
        font-family: monospace, sans-serif;
    }}

    .sub-stat {{
        color: #94a3b8;
        font-size: 11px;
        font-weight: 500;
    }}

    .dim-label {{
        color: #64748b;
        font-size: 10px;
        font-weight: 600;
    }}

    .detail-val {{
        color: #e2e8f0;
        font-size: 11px;
        font-weight: 600;
        font-family: monospace, sans-serif;
    }}

    /* Progress Bars Common */
    progressbar trough {{
        background-color: rgba(255, 255, 255, 0.08);
        border-radius: 6px;
        min-height: 8px;
        border: none;
        padding: 0;
    }}

    /* CPU Progress Bar (Cyan -> Blue) */
    progressbar.cpu-bar progress {{
        background-image: linear-gradient(to right, #06b6d4, #3b82f6);
        border-radius: 6px;
        box-shadow: 0 0 10px rgba(6, 182, 212, 0.5);
    }}

    /* RAM Progress Bar (Light Blue: Cyan -> Blue) */
    progressbar.ram-bar progress {{
        background-image: linear-gradient(to right, #06b6d4, #3b82f6);
        border-radius: 6px;
        box-shadow: 0 0 10px rgba(6, 182, 212, 0.5);
    }}

    /* SSD Health Progress Bar (Light Blue: Cyan -> Blue) */
    progressbar.ssd-bar-good progress {{
        background-image: linear-gradient(to right, #06b6d4, #3b82f6);
        border-radius: 6px;
        box-shadow: 0 0 10px rgba(6, 182, 212, 0.5);
    }}

    progressbar.ssd-bar-warn progress {{
        background-image: linear-gradient(to right, #f59e0b, #ef4444);
        border-radius: 6px;
        box-shadow: 0 0 10px rgba(245, 158, 11, 0.5);
    }}

    /* Per-core mini bars */
    progressbar.core-bar trough {{
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 3px;
        min-height: 4px;
        min-width: 14px;
    }}

    progressbar.core-bar progress {{
        background-image: linear-gradient(to right, #38bdf8, #818cf8);
        border-radius: 3px;
    }}

    /* Health Badges */
    .badge-excellent {{
        background-color: rgba(16, 185, 129, 0.18);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.4);
        border-radius: 8px;
        padding: 2px 8px;
        font-weight: 800;
        font-size: 11px;
    }}

    .badge-good {{
        background-color: rgba(6, 182, 212, 0.18);
        color: #38bdf8;
        border: 1px solid rgba(6, 182, 212, 0.4);
        border-radius: 8px;
        padding: 2px 8px;
        font-weight: 800;
        font-size: 11px;
    }}

    .badge-warn {{
        background-color: rgba(245, 158, 11, 0.18);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.4);
        border-radius: 8px;
        padding: 2px 8px;
        font-weight: 800;
        font-size: 11px;
    }}

    .badge-crit {{
        background-color: rgba(239, 68, 68, 0.25);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.5);
        border-radius: 8px;
        padding: 2px 8px;
        font-weight: 800;
        font-size: 11px;
    }}

    /* Compact Mode Elements */
    .compact-pill {{
        background-color: {pill_bg};
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 4px 12px;
    }}

    .compact-label {{
        color: #94a3b8;
        font-size: 11px;
        font-weight: 700;
    }}

    .compact-val {{
        font-size: 12px;
        font-weight: 800;
        font-family: monospace, sans-serif;
    }}

    /* Menu Styling */
    menu {{
        background-color: rgba(15, 23, 42, 0.94);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 10px;
        padding: 4px;
    }}

    menuitem {{
        color: #e2e8f0;
        border-radius: 6px;
        padding: 5px 10px;
    }}

    menuitem:hover {{
        background-color: rgba(56, 189, 248, 0.2);
        color: #ffffff;
    }}
    """
