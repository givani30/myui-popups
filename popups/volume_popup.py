#!/usr/bin/env python3
"""
Volume Control Popup using MyUI
===============================

A volume control popup with real PulseAudio integration
using the MyUI toolkit.
"""

import sys
import subprocess
from pathlib import Path

# Add current directory to path so we can import myui
sys.path.insert(0, str(Path(__file__).parent.parent))

from widgets.myui import AppWindow, SliderRow, ToggleRow, ButtonRow, QuickApp


class VolumePopup(AppWindow):
    """Volume control popup with mute toggle and preset buttons."""
    
    def __init__(self, app, **kwargs):
        # Extract window_tag and pass other kwargs to parent
        window_tag = kwargs.pop('window_tag', 'volume')
        super().__init__(
            app=app, 
            title="Volume Control",
            width=320,
            window_tag=window_tag,
            close_on_focus_loss=True,
            **kwargs
        )
        
        # Add title
        self.add_title("Audio Control", "Adjust volume and audio settings")
        
        # Get current volume and mute state
        initial_volume = self.get_current_volume()
        is_muted = self.get_mute_state()
        
        # Main volume slider
        self.volume_slider = SliderRow(
            icon="",  # Font Awesome volume icon
            text="Master Volume",
            initial_value=initial_volume,
            callback=self.on_volume_change,
            show_value=True
        )
        self.add_widget(self.volume_slider)
        
        # Mute toggle
        self.mute_toggle = ToggleRow(
            icon="",  # Font Awesome mute icon
            title="Mute",
            subtitle="Temporarily disable audio",
            initial_state=is_muted,
            callback=self.on_mute_toggle
        )
        self.add_widget(self.mute_toggle)
        
        self.add_separator()
        
        # Quick preset buttons
        preset_buttons = ButtonRow(spacing=8)
        preset_buttons.add_button("25%", lambda b: self.set_volume(25))
        preset_buttons.add_button("50%", lambda b: self.set_volume(50))
        preset_buttons.add_button("75%", lambda b: self.set_volume(75))
        preset_buttons.add_button("100%", lambda b: self.set_volume(100))
        self.add_widget(preset_buttons)

    def get_current_volume(self):
        """Get the current system volume as a percentage."""
        try:
            result = subprocess.run(
                ['pactl', 'get-sink-volume', '@DEFAULT_SINK@'],
                capture_output=True, text=True, check=True
            )
            # Parse output like "Volume: front-left: 65536 /  100% / 0.00 dB"
            for line in result.stdout.split('\n'):
                if 'Volume:' in line:
                    # Extract percentage
                    parts = line.split()
                    for part in parts:
                        if part.endswith('%'):
                            return int(part.rstrip('%'))
        except subprocess.CalledProcessError:
            pass
        return 50  # Default if command fails

    def get_mute_state(self):
        """Get the current mute state."""
        try:
            result = subprocess.run(
                ['pactl', 'get-sink-mute', '@DEFAULT_SINK@'],
                capture_output=True, text=True, check=True
            )
            return 'yes' in result.stdout.lower()
        except subprocess.CalledProcessError:
            return False

    def on_volume_change(self, slider):
        """Handle volume slider changes."""
        value = int(slider.get_value())
        print(f" Volume set to {value}%")
        
        # Set actual system volume
        try:
            subprocess.run(['pactl', 'set-sink-volume', '@DEFAULT_SINK@', f'{value}%'], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error setting volume: {e}")
        
        # Update mute state based on volume
        if value == 0 and not self.mute_toggle.get_active():
            self.mute_toggle.set_active(True)
        elif value > 0 and self.mute_toggle.get_active():
            self.mute_toggle.set_active(False)

    def on_mute_toggle(self, switch, state):
        """Handle mute toggle."""
        if state:
            print(" Audio muted")
        else:
            print(" Audio unmuted")
            
        # Toggle actual system mute
        try:
            subprocess.run(['pactl', 'set-sink-mute', '@DEFAULT_SINK@', 'toggle'], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error toggling mute: {e}")
    
    def set_volume(self, volume: int):
        """Set volume to a specific percentage."""
        self.volume_slider.set_value(volume)
        print(f" Volume preset: {volume}%")
        # The slider callback will handle the actual system volume change


if __name__ == "__main__":
    app = QuickApp(
        application_id="com.myui.VolumeControl",
        window_class=VolumePopup,
        window_tag="volume"  # Tag for Hyprland window management
    )
    app.run_quick()
