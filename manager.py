#!/usr/bin/env python3
"""
MyUI Popups Manager
===================

A single, long-running script that manages all popup windows.
This eliminates the startup overhead of launching Python and GTK
for each popup, making them appear quicker.

Usage:
    ./manager.py brightness   # Show brightness popup
    ./manager.py volume       # Show volume popup  
    ./manager.py systeminfo   # Show system info popup
    ./manager.py gallery      # Show widget gallery
"""

import sys
import signal
from pathlib import Path
import gi

# Add project to path so we can import widgets and popups
sys.path.insert(0, str(Path(__file__).parent))

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw

# Import all popup window classes
from popups.brightness_popup import BrightnessPopup
from popups.volume_popup import VolumePopup  
from popups.battery_popup import BatteryPopup
from popups.bluetooth_popup import BluetoothPopup
from popups.network_popup import NetworkPopup
from popups.system_info_popup import SystemInfoPopup
from popups.widget_showcase import WidgetShowcase

# Keep track of open windows to prevent duplicates
open_windows = {}


class PopupManager(Adw.Application):
    """
    Application that runs as a daemon to manage popups.
    """
    
    def __init__(self, application_id="org.myui.PopupManager"):
        super().__init__(application_id=application_id)
        # Set flags for command line handling only (remove service flag for now)
        self.set_flags(gi.repository.Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        # Connect signal handler for graceful shutdown
        signal.signal(signal.SIGTERM, self.handle_shutdown)
    
    def handle_shutdown(self, signum, frame):
        """Handler for SIGTERM to ensure a clean exit."""
        print("INFO: Manager received shutdown signal. Exiting gracefully.")
        self.quit()

    def do_startup(self):
        """
        Called once when the application starts.
        We use this to take a "hold" on the application, preventing it from
        quitting automatically when there are no windows.
        """
        Adw.Application.do_startup(self)
        self.hold()  # This is the crucial call
        
    def do_activate(self):
        """
        Called when the application is activated (daemon mode without args).
        """
        # Don't call parent activate - we don't want default window behavior
        pass

    def do_command_line(self, command_line):
        """Handle command-line arguments to show specific popups.""" 
        try:
            args = command_line.get_arguments()
            
            if len(args) < 2:
                # No arguments provided - this is normal for daemon startup
                # Don't activate, just let the service stay running
                return 0

            popup_name = args[1]
            self.activate()  # Activate when we have a specific popup request
            
            # If window is already open, bring it to front or close it (toggle behavior)
            if popup_name in open_windows and open_windows[popup_name].is_visible():
                open_windows[popup_name].close()
                return 0

            # Map argument to window class
            popup_map = {
                "brightness": BrightnessPopup,
                "volume": VolumePopup,
                "battery": BatteryPopup,
                "systeminfo": SystemInfoPopup,
                "bluetooth": BluetoothPopup,
                "network": NetworkPopup,
                "showcase": WidgetShowcase
            }

            if popup_name in popup_map:
                window_class = popup_map[popup_name]
                
                # Create new popup window
                new_window = window_class(app=self, window_tag=popup_name)
                open_windows[popup_name] = new_window
                
                # Clean up when window closes
                def on_window_closed(window):
                    if popup_name in open_windows:
                        del open_windows[popup_name]
                
                new_window.connect('destroy', lambda w: on_window_closed(w))
                new_window.present()
            else:
                print(f"Error: Unknown popup '{popup_name}'")
                print("Available: brightness, volume, battery, systeminfo, bluetooth, network, showcase")

        except Exception as e:
            print(f"FATAL: An error occurred in the popup manager: {e}", file=sys.stderr)
            # Write error to log file for debugging
            with open("/tmp/myui_manager.log", "a") as log_file:
                log_file.write(f"Error at {__file__}: {e}\n")

        return 0


if __name__ == "__main__":
    app = PopupManager()
    sys.exit(app.run(sys.argv))