#!/usr/bin/env python3
"""
Battery Limit Popup using MyUI
===============================

A clean implementation of the battery limit control popup using
the MyUI toolkit.
"""

import sys
import subprocess
from pathlib import Path

# Add current directory to path so we can import myui
sys.path.insert(0, str(Path(__file__).parent.parent))

from widgets.myui.components.widgets import SliderRow
from widgets.myui import AppWindow  
from widgets.myui.base_window import QuickApp


class BatteryPopup(AppWindow):
    """Battery charging limit control popup using MyUI components."""
    
    def __init__(self, app, **kwargs):
        # Extract window_tag and pass other kwargs to parent
        window_tag = kwargs.pop('window_tag', 'battery')
        super().__init__(
            app=app, 
            title="Battery Charging Limit",
            width=350,
            window_tag=window_tag,
            **kwargs
        )
        
        # Add title
        self.add_title("Battery Charging Limit", "Protect battery longevity")
        
        # Get current battery limit
        current_limit = self.get_current_limit()
        
        # Battery limit slider
        battery_slider = SliderRow(
            icon="󱊣",
            text="Charging Limit",
            initial_value=current_limit,
            min_val=50,
            max_val=100,
            step=5,
            callback=self.on_limit_change,
            show_value=True
        )
        self.add_widget(battery_slider)

    def get_current_limit(self):
        """Get the current battery charging limit."""
        try:
            with open('/sys/class/power_supply/BAT0/charge_control_end_threshold', 'r') as f:
                return int(f.read().strip())
        except (FileNotFoundError, ValueError, PermissionError):
            return 80  # Default fallback

    def on_limit_change(self, slider):
        """Handle battery limit change."""
        value = int(slider.get_value())
        print(f"INFO: Battery charging limit set to {value}%")
        
        # Set the battery limit using the battery-limit command
        try:
            subprocess.run([str(Path.home() / '.local/bin/battery-limit'), 'set', str(value)], 
                         check=True)
            
            # Save the limit for persistence
            config_file = Path.home() / '.config/battery-limit.conf'
            config_file.write_text(str(value))
            
            # Signal waybar to refresh
            subprocess.run(['pkill', '-SIGRTMIN+11', 'waybar'], check=False)
            
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to set battery limit: {e}")
        except Exception as e:
            print(f"ERROR: Unexpected error: {e}")


if __name__ == "__main__":
    app = QuickApp(
        application_id="com.example.BatteryLimit",
        window_class=BatteryPopup,
        window_tag="battery"
    )
    app.run_quick()