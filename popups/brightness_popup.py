#!/usr/bin/env python3
"""
Brightness Popup using MyUI
===========================

This is a clean implementation of the brightness control popup using
the new MyUI toolkit. Compare this to the original slidertest.py!
"""

import sys
import subprocess
from pathlib import Path

# Add current directory to path so we can import myui
sys.path.insert(0, str(Path(__file__).parent))

from widgets.myui.components.widgets import SliderRow, ToggleRow
from widgets.myui import AppWindow  
from widgets.myui.base_window import QuickApp


class BrightnessPopup(AppWindow):
    """Clean brightness control popup using MyUI components."""
    
    def __init__(self, app, **kwargs):
        # Extract window_tag and pass other kwargs to parent
        window_tag = kwargs.pop('window_tag', 'brightness')
        super().__init__(
            app=app, 
            title="Brightness Control",
            width=350,
            window_tag=window_tag,
            close_on_focus_loss=True,  # Keep open for fine adjustments
            **kwargs
        )
        
        # Add title
        self.add_title("Display Brightness", "Adjust screen brightness levels")
        
        # Laptop display slider
        laptop_slider = SliderRow(
            icon="󰃟",
            text="Laptop Display",
            initial_value=75,
            callback=self.on_laptop_change,
            show_value=True
        )
        self.add_widget(laptop_slider)

        # External monitor slider (only update on release due to ddcutil lag)
        external_slider = SliderRow(
            icon="󰍹",
            text="External Monitor", 
            initial_value=50,
            on_release_callback=self.on_external_change,
            show_value=True
        )
        self.add_widget(external_slider)

        # Add separator
        self.add_separator()

        # Theme toggle
        theme_toggle = ToggleRow(
            icon="󰌵",
            title="Light Theme",
            subtitle="Toggle between light and dark theme",
            initial_state=self.get_current_theme_mode() == "light",
            callback=self.on_theme_toggle
        )
        self.add_widget(theme_toggle)

    def on_laptop_change(self, slider):
        """Handle laptop brightness change."""
        value = int(slider.get_value())
        print(f"INFO: Laptop brightness set to {value}%")
        # Here you would call: subprocess.run(['brightnessctl', 'set', f'{value}%'])
        subprocess.run(['brightnessctl', 'set', f'{value}%'])

    def on_external_change(self, slider):
        """Handle external monitor brightness change."""
        value = int(slider.get_value())
        print(f"DEBUG: on_external_change called with value {value}%")
        print(f"INFO: External monitor brightness set to {value}%")
        # Here you would call: subprocess.run(['ddcutil', 'setvcp', '10', str(value)])
        subprocess.run(['ddcutil', 'setvcp', '10', str(value)])

    def get_current_theme_mode(self):
        """Get the current theme mode from cache file."""
        try:
            mode_cache = Path.home() / ".cache" / "matugen-mode"
            if mode_cache.exists():
                return mode_cache.read_text().strip()
        except Exception:
            pass
        return "dark"  # default

    def on_theme_toggle(self, switch, state):
        """Handle theme toggle."""
        mode = "light" if state else "dark"
        print(f"INFO: Switching to {mode} theme")
        
        try:
            # Call the toggle script - use 'toggle' to ensure consistent behavior
            script_path = Path.home() / ".config" / "hypr" / "scripts" / "toggle-theme.sh"
            subprocess.run([str(script_path), "toggle"], check=True)
        except Exception as e:
            print(f"ERROR: Failed to toggle theme: {e}")


if __name__ == "__main__":
    app = QuickApp(
        application_id="com.example.BrightnessControl",
        window_class=BrightnessPopup,
        window_tag="brightness"
    )
    app.run_quick()
