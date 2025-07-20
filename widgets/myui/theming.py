"""
Theming module for MyUI
======================

Handles loading CSS from various sources and applying themes to GTK applications.
Automatically detects and loads your Waybar colors.css or provides fallbacks.
"""

import sys
from pathlib import Path

import gi
from gi.repository import Gtk, Gdk
gi.require_version('Gtk', '4.0')

def _find_colors_css():
    """Find colors.css in multiple possible locations."""
    possible_paths = [
        Path(__file__).parent.parent / 'colors.css',  # Local waybar_popups colors.css (highest priority)
        Path.home() / '.config' / 'waybar' / 'colors.css',  # Waybar colors.css (fallback)
        Path.cwd() / 'colors.css',  # Current working directory
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    return None

def _get_full_css() -> str:
    """Finds Waybar colors and merges them with default widget styles."""
    waybar_css = ""
    fallback_css = """
    /* --- Fallback Colors (Catppuccin-inspired) --- */
    @define-color background #1e1e2e;
    @define-color surface_container #282a36;
    @define-color surface_variant #45475a;
    @define-color primary #89b4fa;
    @define-color on_surface #cdd6f4;
    @define-color on_primary #1e1e2e;
    @define-color error #f38ba8;
    @define-color on_error #1e1e2e;
    @define-color outline #6c7086;
    """
    
    try:
        colors_file = _find_colors_css()
        if colors_file:
            waybar_css = colors_file.read_text()
            print(f"DEBUG: Loaded colors from {colors_file}", file=sys.stderr)
        else:
            print("DEBUG: No colors.css found, using fallback", file=sys.stderr)
    except Exception as e:
        print(f"DEBUG: Could not read colors CSS, using fallback. Error: {e}", file=sys.stderr)

    # Widget-specific styling that works with any color scheme
    widget_css = """
    /* --- Window Styling --- */
    window {
        background-color: alpha(@surface_container, 0.9);
        border-radius: 14px;
        border: 1px solid rgba(0, 0, 0, 0.2);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    }
    
    /* --- Typography --- */
    label {
        color: @on_surface;
        font-family: "Inter", "SF Pro Display", sans-serif;
        font-size: 11pt;
    }
    
    .icon-label {
        font-family: "IosevkaTerm Nerd Font Mono", "Symbols Nerd Font", monospace;
        font-size: 14pt;
        color: @primary;
    }
    
    .title-label {
        font-size: 13pt;
        font-weight: 600;
        color: @on_surface;
    }
    
    .subtitle-label {
        font-size: 10pt;
        color: @outline;
    }
    
    /* --- Slider Styling (High Specificity) --- */
    window scale {
        border: none;
        background: none;
    }

    window scale trough {
        background-color: @surface_variant;
        border-radius: 8px;
        min-height: 10px;
        border: 1px solid rgba(0, 0, 0, 0.1);
    }

    window scale highlight {
        background-color: @primary;
        border-radius: 8px;
    }

    /* Target the circular handle */
    window scale slider {
        background-color: @primary;
        border: 2px solid @on_primary;
        border-radius: 50%;
        min-width: 18px;
        min-height: 18px;
        margin: -6px; /* Adjusts handle position */
    }

    window scale slider:hover {
        box-shadow: 0 0 0 4px alpha(@primary, 0.3); /* Creates a glow effect on hover */
    }

    /* Hides the default GTK indicator, we use our own 'slider' style */
    window scale indicator {
        background-image: none;
        border: none;
    }
    
    /* --- Button Styling --- */
    button {
        background-color: @surface_variant;
        border: 1px solid @outline;
        border-radius: 8px;
        padding: 8px 16px;
        color: @on_surface;
        font-family: "Inter", sans-serif;
        font-size: 10pt;
    }
    
    button:hover {
        background-color: @primary;
        color: @on_primary;
    }
    
    button.destructive {
        background-color: #f38ba8;
        color: #1e1e2e;
        border-color: #f38ba8;
    }
    
    /* --- List and Row Styling --- */
    .info-row {
        padding: 8px 0;
        border-bottom: 1px solid @outline;
    }
    
    .info-row:last-child {
        border-bottom: none;
    }
    """
    
    # Combine colors with widget styling
    if waybar_css:
        return waybar_css + widget_css
    else:
        return fallback_css + widget_css

def apply_theme():
    """Applies the combined CSS to the entire application."""
    css_provider = Gtk.CssProvider()
    css_provider.load_from_string(_get_full_css())
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(), 
        css_provider, 
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

def get_css_string() -> str:
    """Returns the full CSS string for debugging purposes."""
    return _get_full_css()
