#!/usr/bin/env python3
"""
Bluetooth Popup with Bleak Integration
======================================

Modern bluetooth management interface using Bleak for reliable device scanning.
Features async device scanning, pairing, connection management, and power control.
"""

import asyncio
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib

# Add current directory to path so we can import myui
sys.path.insert(0, str(Path(__file__).parent))

from widgets.myui import AppWindow, QuickApp, ListWidget, LoadingWidget, ButtonRow, ToggleRow, run_async

# Import Bleak for modern bluetooth functionality
try:
    from bleak import BleakScanner, BleakClient
    from bleak.backends.device import BLEDevice
    BLEAK_AVAILABLE = True
except ImportError:
    BLEAK_AVAILABLE = False
    print("Warning: Bleak not available, falling back to bluetoothctl")


class BluetoothDevice:
    """Represents a bluetooth device with its properties."""
    
    def __init__(self, mac: str, name: str, paired: bool = False, connected: bool = False, trusted: bool = False, rssi: int = None):
        self.mac = mac
        self.name = name or "Unknown Device"
        self.paired = paired
        self.connected = connected
        self.trusted = trusted
        self.rssi = rssi
        self.device_type = "Unknown"
        
    def __repr__(self):
        status = []
        if self.connected:
            status.append("Connected")
        if self.paired:
            status.append("Paired")
        if self.trusted:
            status.append("Trusted")
        
        status_str = f" ({', '.join(status)})" if status else ""
        rssi_str = f" [{self.rssi}dBm]" if self.rssi else ""
        return f"{self.name}{status_str}{rssi_str}"
        
    def get_icon(self) -> str:
        """Get appropriate icon for device type and status."""
        if self.connected:
            return "󰂯"  # Connected
        elif self.paired:
            return "󰂲"  # Paired but disconnected
        else:
            return "󰂱"  # Unpaired


class BluetoothManager:
    """Handles bluetooth operations using Bleak and bluetoothctl."""
    
    def __init__(self):
        self.scanning = False
        self.bleak_available = BLEAK_AVAILABLE
        
    def get_bluetooth_status(self) -> bool:
        """Check if bluetooth is powered on."""
        try:
            result = subprocess.run(
                ["bluetoothctl", "show"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            for line in result.stdout.split('\n'):
                if "Powered:" in line:
                    return "yes" in line.lower()
            return False
        except Exception:
            return False
            
    def set_bluetooth_power(self, enabled: bool) -> bool:
        """Turn bluetooth on or off."""
        try:
            command = "on" if enabled else "off"
            result = subprocess.run(
                ["bluetoothctl", "power", command],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
            
    def get_paired_devices(self) -> List[BluetoothDevice]:
        """Get list of paired devices with their connection status."""
        devices = []
        
        try:
            # Get paired devices
            result = subprocess.run(
                ["bluetoothctl", "devices", "Paired"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            for line in result.stdout.strip().split('\n'):
                if not line.strip():
                    continue
                    
                parts = line.split(' ', 2)
                if len(parts) >= 3:
                    mac = parts[1]
                    name = parts[2]
                    
                    # Check connection status
                    connected = self._is_device_connected(mac)
                    device = BluetoothDevice(mac, name, paired=True, connected=connected, trusted=True)
                    devices.append(device)
                    
        except Exception as e:
            print(f"Error getting paired devices: {e}")
            
        return devices
        
    def _is_device_connected(self, mac: str) -> bool:
        """Check if a specific device is connected."""
        try:
            result = subprocess.run(
                ["bluetoothctl", "info", mac],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            return "Connected: yes" in result.stdout
        except Exception:
            return False
    
    async def scan_devices_async(self, progress_callback=None, duration=10) -> List[BluetoothDevice]:
        """Scan for bluetooth devices using Bleak (async)."""
        if not self.bleak_available:
            raise Exception("Bleak not available")
            
        devices = []
        
        try:
            # Track last update time to throttle UI updates
            last_update_time = 0
            
            def detection_callback(device: BLEDevice, advertisement_data):
                nonlocal last_update_time
                
                # Create our device object
                bt_device = BluetoothDevice(
                    mac=device.address,
                    name=device.name or advertisement_data.local_name or "Unknown Device",
                    rssi=advertisement_data.rssi
                )
                
                # Avoid duplicates
                if not any(d.mac == bt_device.mac for d in devices):
                    devices.append(bt_device)
                    
                    # Throttle updates to avoid GTK issues (max once per second)
                    import time
                    current_time = time.time()
                    if progress_callback and (current_time - last_update_time) >= 1.0:
                        progress_callback("device_found", devices.copy(), f"Found {len(devices)} devices")
                        last_update_time = current_time
            
            # Start scanning
            if progress_callback:
                progress_callback("progress", 0.1, "Starting Bleak scan...")
            
            async with BleakScanner(detection_callback=detection_callback) as scanner:
                # Scan for the specified duration
                scan_step = 0.5  # Update every 0.5 seconds
                steps = int(duration / scan_step)
                
                for i in range(steps):
                    await asyncio.sleep(scan_step)
                    progress = (i + 1) / steps
                    if progress_callback:
                        progress_callback("progress", progress, f"Scanning... {i * scan_step:.1f}s")
                
                # Give final update
                if progress_callback:
                    progress_callback("progress", 1.0, f"Scan complete! Found {len(devices)} devices")
                    
        except Exception as e:
            raise Exception(f"Bleak scan failed: {e}")
            
        return devices
    
    def scan_devices_sync(self, progress_callback=None) -> Dict[str, any]:
        """
        Synchronous wrapper for async bluetooth scanning.
        This is designed to be run in a background thread.
        """
        try:
            # Run the async scan
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            devices = loop.run_until_complete(
                self.scan_devices_async(progress_callback=progress_callback)
            )
            
            loop.close()
            
            return {
                "success": True,
                "devices": devices,
                "total_found": len(devices)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "devices": [],
                "total_found": 0
            }
            
    def connect_device(self, mac: str) -> bool:
        """Connect to a device."""
        try:
            result = subprocess.run(
                ["bluetoothctl", "connect", mac],
                capture_output=True,
                text=True,
                timeout=15
            )
            return result.returncode == 0
        except Exception:
            return False
            
    def disconnect_device(self, mac: str) -> bool:
        """Disconnect from a device."""
        try:
            result = subprocess.run(
                ["bluetoothctl", "disconnect", mac],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
            
    def pair_device(self, mac: str) -> bool:
        """Pair with a device."""
        try:
            # Pair
            pair_result = subprocess.run(
                ["bluetoothctl", "pair", mac],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if pair_result.returncode == 0:
                # Trust
                subprocess.run(
                    ["bluetoothctl", "trust", mac],
                    capture_output=True,
                    timeout=5
                )
                return True
            return False
        except Exception:
            return False
            
    def unpair_device(self, mac: str) -> bool:
        """Unpair/remove a device."""
        try:
            # First disconnect if connected
            self.disconnect_device(mac)
            
            # Remove (unpair)
            result = subprocess.run(
                ["bluetoothctl", "remove", mac],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False


class BluetoothPopup(AppWindow):
    """Main bluetooth management popup with Bleak integration."""
    
    def __init__(self, app, **kwargs):
        # Extract window_tag and pass other kwargs to parent
        window_tag = kwargs.pop('window_tag', 'bluetooth')
        super().__init__(
            app=app,
            title="Bluetooth Manager",
            window_tag=window_tag,
            width=380,
            height=520,
            close_on_focus_loss=True,
            **kwargs
        )
        
        self.bt_manager = BluetoothManager()
        self.current_scan_thread = None
        self.paired_devices = []
        self.discoverable_devices = []
        
        self.setup_ui()
        self.refresh_device_lists()
        
    def setup_ui(self):
        """Set up the UI components."""
        # Header with power control
        self.setup_power_control()
        self.main_box.append(Gtk.Separator())
        
        # Control buttons
        self.setup_control_buttons()
        self.main_box.append(Gtk.Separator())
        
        # Scan progress
        self.setup_scan_progress()
        self.main_box.append(Gtk.Separator())
        
        # Device lists
        self.setup_device_lists()
        
        # Bottom buttons
        self.setup_bottom_buttons()
        
    def setup_power_control(self):
        """Set up bluetooth power on/off control."""
        power_status = self.bt_manager.get_bluetooth_status()
        
        self.power_toggle = ToggleRow(
            icon="󰂐",
            title="Bluetooth Power",
            subtitle="Enable or disable bluetooth adapter",
            initial_state=power_status,
            callback=self.on_power_toggle
        )
        self.main_box.append(self.power_toggle)
        
    def setup_control_buttons(self):
        """Set up scan and settings buttons."""
        # Scan button
        self.scan_button = ButtonRow()
        self.scan_btn = self.scan_button.add_button(
            "Start Scan",
            callback=self.on_scan_clicked,
            icon="󰤄"
        )
        self.main_box.append(self.scan_button)
        self.scanning_active = False
        
        # Refresh button
        button_row = ButtonRow()
        self.refresh_button = button_row.add_button(
            "Refresh Paired",
            callback=self.refresh_device_lists,
            icon="󰑐"
        )
        self.main_box.append(button_row)
        
    def setup_scan_progress(self):
        """Set up scan progress indicator."""
        self.loading_widget = LoadingWidget(
            text="Ready to scan",
            show_spinner=False
        )
        self.main_box.append(self.loading_widget)
        
    def setup_device_lists(self):
        """Set up paired and discoverable device lists."""
        # Paired devices
        paired_label = Gtk.Label(label="Paired Devices", xalign=0)
        paired_label.add_css_class("title-label")
        self.main_box.append(paired_label)
        
        self.paired_list = ListWidget(height=150)
        self.main_box.append(self.paired_list)
        
        # Discoverable devices
        discoverable_label = Gtk.Label(label="Available Devices", xalign=0)
        discoverable_label.add_css_class("title-label")
        self.main_box.append(discoverable_label)
        
        self.discoverable_list = ListWidget(height=150)
        self.main_box.append(self.discoverable_list)
        
    def on_power_toggle(self, switch, state):
        """Handle bluetooth power toggle."""
        if self.bt_manager.set_bluetooth_power(state):
            status = "enabled" if state else "disabled"
            self.show_notification(f"Bluetooth {status}")
            
            # Update UI based on power state
            self.scan_btn.set_sensitive(state)
            self.refresh_button.set_sensitive(state)
            
            if state:
                self.refresh_device_lists()
            else:
                # Clear device lists when bluetooth is off
                self.paired_list.clear_items()
                self.discoverable_list.clear_items()
        else:
            self.show_notification("Failed to change bluetooth power")
            # Revert switch state
            switch.set_active(not state)
            
    def on_scan_clicked(self, button):
        """Handle scan button clicks."""
        if self.scanning_active:
            self.stop_scan()
        else:
            self.start_scan()
            
    def start_scan(self):
        """Start bluetooth device scanning using Bleak."""
        if self.current_scan_thread or not self.bt_manager.get_bluetooth_status():
            return
            
        if not self.bt_manager.bleak_available:
            self.show_notification("Bleak not available, cannot scan")
            return
            
        # Update UI
        self.scanning_active = True
        self.scan_btn.set_label("Stop Scan")
        self.loading_widget.set_spinning(True)
        self.loading_widget.set_text("Scanning for devices...")
        
        # Clear previous discoverable devices
        self.discoverable_devices = []
        self.update_discoverable_list()
        
        # Start Bleak scan
        self.current_scan_thread = run_async(
            target_func=self.bt_manager.scan_devices_sync,
            success_callback=self.on_scan_complete,
            error_callback=self.on_scan_error,
            progress_callback=self.on_scan_progress,
            thread_name="bleak_scan"
        )
        
    def stop_scan(self):
        """Stop ongoing device scan."""
        if self.current_scan_thread:
            from widgets.myui import cancel_async
            cancel_async(self.current_scan_thread)
            self.current_scan_thread = None
            
        # Reset UI
        self.scanning_active = False
        self.scan_btn.set_label("Start Scan")
        self.loading_widget.set_spinning(False)
        self.loading_widget.set_text("Scan stopped")
        
    def on_scan_progress(self, event_type, *args):
        """Handle scan progress updates."""
        if event_type == "progress":
            progress, status = args
            # Ensure UI updates happen on main thread
            from gi.repository import GLib
            GLib.idle_add(self._update_progress_text, status)
        elif event_type == "device_found":
            devices_list, status = args
            # Ensure UI updates happen on main thread
            from gi.repository import GLib
            GLib.idle_add(self._update_device_list_safe, devices_list, status)
    
    def _update_progress_text(self, status):
        """Safely update progress text on main thread."""
        self.loading_widget.set_text(status)
        return False  # Don't repeat
        
    def _update_device_list_safe(self, devices_list, status):
        """Safely update device list on main thread."""
        try:
            self.loading_widget.set_text(status)
            self.discoverable_devices = devices_list
            self.update_discoverable_list()
        except Exception as e:
            print(f"Error updating device list: {e}")
        return False  # Don't repeat
            
    def on_scan_complete(self, result):
        """Handle scan completion."""
        self.current_scan_thread = None
        self.scanning_active = False
        self.scan_btn.set_label("Start Scan")
        self.loading_widget.set_spinning(False)
        
        if result["success"]:
            self.discoverable_devices = result["devices"]
            self.update_discoverable_list()
            
            self.loading_widget.set_text(f"Scan complete! Found {result['total_found']} devices")
        else:
            error = result.get("error", "Unknown error")
            self.loading_widget.set_text(f"Scan failed: {error}")
            
    def on_scan_error(self, error):
        """Handle scan errors."""
        self.current_scan_thread = None
        self.scanning_active = False
        self.scan_btn.set_label("Start Scan")
        self.loading_widget.set_spinning(False)
        self.loading_widget.set_text(f"Scan error: {error}")
        
    def refresh_device_lists(self, button=None):
        """Refresh both paired and discoverable device lists."""
        if not self.bt_manager.get_bluetooth_status():
            return
            
        self.paired_devices = self.bt_manager.get_paired_devices()
        self.update_paired_list()
        
    def update_paired_list(self):
        """Update the paired devices list."""
        self.paired_list.clear_items()
        
        if not self.paired_devices:
            self.paired_list.add_item("ℹ️", "No paired devices", "Pair devices to see them here")
            return
            
        for device in self.paired_devices:
            subtitle = f"{device.mac}"
            if device.connected:
                subtitle += " • Connected"
            else:
                subtitle += " • Click to connect, right-click to unpair"
            
            self.paired_list.add_item(
                device.get_icon(),
                device.name,
                subtitle,
                callback=self.on_paired_device_clicked,
                right_click_callback=self.on_paired_device_right_clicked,
                data=device
            )
            
    def update_discoverable_list(self):
        """Update the discoverable devices list."""
        self.discoverable_list.clear_items()
        
        if not self.discoverable_devices:
            self.discoverable_list.add_item("ℹ️", "No devices found", "Scan for devices to see them here")
            return
            
        for device in self.discoverable_devices:
            subtitle = f"{device.mac}"
            if device.rssi:
                subtitle += f" • {device.rssi}dBm"
            subtitle += " • Tap to pair"
            
            self.discoverable_list.add_item(
                device.get_icon(),
                device.name,
                subtitle,
                callback=self.on_discoverable_device_clicked,
                data=device
            )
            
    def on_paired_device_clicked(self, row, device: BluetoothDevice):
        """Handle paired device selection (connect/disconnect)."""
        # Show progress
        action = "Disconnecting" if device.connected else "Connecting"
        self.loading_widget.set_spinning(True)
        self.loading_widget.set_text(f"{action} {device.name}...")
        
        # Connect/disconnect in background to avoid UI freeze
        def connection_worker():
            if device.connected:
                return self.bt_manager.disconnect_device(device.mac)
            else:
                return self.bt_manager.connect_device(device.mac)
        
        def on_connection_success(success):
            self.loading_widget.set_spinning(False)
            if success:
                action = "Disconnected from" if device.connected else "Connected to"
                self.show_notification(f"{action} {device.name}")
                self.refresh_device_lists()
                self.loading_widget.set_text("Ready to scan")
            else:
                action = "disconnect from" if device.connected else "connect to"
                self.show_notification(f"Failed to {action} {device.name}")
                self.loading_widget.set_text("Connection failed")
        
        def on_connection_error(error):
            self.loading_widget.set_spinning(False)
            self.show_notification(f"Connection error: {error}")
            self.loading_widget.set_text("Connection failed")
        
        run_async(
            target_func=connection_worker,
            success_callback=on_connection_success,
            error_callback=on_connection_error,
            thread_name="bluetooth_connect"
        )
        
    def on_paired_device_right_clicked(self, row, device: BluetoothDevice):
        """Handle right-click on paired device (unpair)."""
        # Show unpair progress
        self.loading_widget.set_spinning(True)
        self.loading_widget.set_text(f"Unpairing {device.name}...")
        
        # Unpair in background
        def unpair_worker():
            return self.bt_manager.unpair_device(device.mac)
        
        def on_unpair_success(success):
            self.loading_widget.set_spinning(False)
            if success:
                self.show_notification(f"Unpaired {device.name}")
                self.refresh_device_lists()
                self.loading_widget.set_text("Ready to scan")
            else:
                self.show_notification(f"Failed to unpair {device.name}")
                self.loading_widget.set_text("Unpair failed")
        
        def on_unpair_error(error):
            self.loading_widget.set_spinning(False)
            self.show_notification(f"Unpair error: {error}")
            self.loading_widget.set_text("Unpair failed")
        
        run_async(
            target_func=unpair_worker,
            success_callback=on_unpair_success,
            error_callback=on_unpair_error,
            thread_name="bluetooth_unpair"
        )
                
    def on_discoverable_device_clicked(self, row, device: BluetoothDevice):
        """Handle discoverable device selection (pair)."""
        # Show pairing progress
        self.loading_widget.set_spinning(True)
        self.loading_widget.set_text(f"Pairing with {device.name}...")
        
        # Pair in background (this can take time)
        def pair_worker():
            return self.bt_manager.pair_device(device.mac)
            
        def on_pair_success(success):
            self.loading_widget.set_spinning(False)
            if success:
                self.show_notification(f"Paired with {device.name}")
                self.refresh_device_lists()
                # Remove from discoverable list
                self.discoverable_devices = [d for d in self.discoverable_devices if d.mac != device.mac]
                self.update_discoverable_list()
                self.loading_widget.set_text("Ready to scan")
            else:
                self.show_notification(f"Failed to pair with {device.name}")
                self.loading_widget.set_text("Pairing failed")
                
        def on_pair_error(error):
            self.loading_widget.set_spinning(False)
            self.show_notification(f"Pairing error: {error}")
            self.loading_widget.set_text("Pairing failed")
            
        run_async(
            target_func=pair_worker,
            success_callback=on_pair_success,
            error_callback=on_pair_error,
            thread_name="bluetooth_pair"
        )
        
    def show_notification(self, message: str):
        """Show system notification."""
        try:
            subprocess.run(
                ["notify-send", "Bluetooth", message],
                capture_output=True,
                timeout=5
            )
        except Exception:
            print(f"Notification: {message}")
            
    def setup_bottom_buttons(self):
        """Set up bottom action buttons."""
        bottom_buttons = ButtonRow()
        
        # Blueman manager button
        bottom_buttons.add_button(
            "Advanced",
            callback=self.open_blueman_manager,
            icon="󰒓"
        )
        
        # Exit button
        bottom_buttons.add_button(
            "Exit",
            callback=lambda btn: self.close(),
            icon="󰅖"
        )
        
        self.main_box.append(Gtk.Separator())
        self.main_box.append(bottom_buttons)
        
    def open_blueman_manager(self, button):
        """Open blueman-manager for advanced configuration."""
        try:
            subprocess.Popen(["blueman-manager"])
            self.show_notification("Opening Blueman Manager")
        except Exception as e:
            self.show_notification(f"Failed to open Blueman Manager: {e}")


if __name__ == "__main__":
    app = QuickApp(
        application_id="com.myui.bluetooth",
        window_class=BluetoothPopup
    )
    app.run()