#!/usr/bin/env python3
"""
Fixed Network Manager Popup - No auto-scan in constructor
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional
import gi

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib

# Add current directory to path so we can import myui
sys.path.insert(0, str(Path(__file__).parent.parent))

from widgets.myui import AppWindow, QuickApp, ListWidget, LoadingWidget, ButtonRow, ToggleRow, InfoRow, run_async

# Import NetworkManager for network operations (using python-sdbus)
try:
    import sdbus
    from sdbus_block.networkmanager import (
        NetworkManager as NMManager,
        NetworkManagerSettings,
        NetworkDeviceGeneric,
        NetworkDeviceWireless,
        AccessPoint,
        ActiveConnection,
    )
    from sdbus_block.networkmanager.enums import DeviceType, DeviceState
    
    # Set system bus as default since NetworkManager uses system D-Bus
    sdbus.set_default_bus(sdbus.sd_bus_open_system())
    
    NM_AVAILABLE = True
    print("Using python-sdbus NetworkManager")
except ImportError:
    NM_AVAILABLE = False
    print("Warning: python-sdbus NetworkManager not available, falling back to nmcli")


class NetworkConnection:
    """Represents a network connection."""
    
    def __init__(self, ssid: str, signal_strength: int = 0, security: str = "", 
                 connected: bool = False, known: bool = False, device_path: str = ""):
        self.ssid = ssid
        self.signal_strength = signal_strength
        self.security = security
        self.connected = connected
        self.known = known  # Previously connected
        self.device_path = device_path
        
    def get_icon(self) -> str:
        """Get appropriate icon for connection type and status."""
        if self.connected:
            return "󰤨"  # Connected WiFi
        elif self.known:
            return "󰤥"  # Known WiFi
        elif self.security:
            return "󰤡"  # Secured WiFi
        else:
            return "󰤢"  # Open WiFi
            
    def get_signal_bars(self) -> str:
        """Get signal strength visual representation."""
        if self.signal_strength >= 80:
            return "▂▄▆█"
        elif self.signal_strength >= 60:
            return "▂▄▆"
        elif self.signal_strength >= 40:
            return "▂▄"
        elif self.signal_strength >= 20:
            return "▂"
        else:
            return "."


class NetworkManager:
    """Handles network operations using NetworkManager."""
    
    def __init__(self):
        print("DEBUG: NetworkManager.__init__ started")
        self.nm_available = NM_AVAILABLE
        self.scanning = False
        
        if self.nm_available:
            try:
                print("DEBUG: Creating NetworkManager instance")
                self.nm = NMManager()
                print("DEBUG: Initializing WiFi devices list")
                self._wifi_devices = []
                print("DEBUG: Refreshing WiFi devices")
                self._refresh_wifi_devices()
                print("DEBUG: NetworkManager initialization complete")
            except Exception as e:
                print(f"Failed to initialize NetworkManager: {e}")
                import traceback
                traceback.print_exc()
                self.nm_available = False
    
    def _refresh_wifi_devices(self):
        """Get list of WiFi devices."""
        if not self.nm_available:
            return
        
        try:
            self._wifi_devices = []
            for device_path in self.nm.devices:
                device = NetworkDeviceGeneric(device_path)
                if device.device_type == DeviceType.WIFI:
                    wifi_device = NetworkDeviceWireless(device_path)
                    self._wifi_devices.append(wifi_device)
        except Exception as e:
            print(f"Error refreshing WiFi devices: {e}")
            self._wifi_devices = []
        
    def get_wifi_enabled(self) -> bool:
        """Check if WiFi is enabled."""
        try:
            if self.nm_available:
                return self.nm.wireless_enabled
            else:
                result = subprocess.run(
                    ["nmcli", "radio", "wifi"],
                    capture_output=True, text=True, timeout=5
                )
                return "enabled" in result.stdout.lower()
        except Exception:
            return False
            
    def get_airplane_mode(self) -> bool:
        """Check if airplane mode is enabled (all radios off)."""
        try:
            result = subprocess.run(
                ["nmcli", "radio", "all"],
                capture_output=True, text=True, timeout=5
            )
            return "disabled" in result.stdout.lower()
        except Exception:
            return False
            
    def set_airplane_mode(self, enabled: bool) -> bool:
        """Enable or disable airplane mode."""
        try:
            command = "off" if enabled else "on"
            result = subprocess.run(
                ["nmcli", "radio", "all", command],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
            
    def set_wifi_enabled(self, enabled: bool) -> bool:
        """Enable or disable WiFi."""
        try:
            command = "on" if enabled else "off"
            result = subprocess.run(
                ["nmcli", "radio", "wifi", command],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
            
    def get_active_connection(self) -> Optional[NetworkConnection]:
        """Get currently active WiFi connection."""
        try:
            result = subprocess.run(
                ["nmcli", "-t", "-f", "NAME,DEVICE,TYPE", "connection", "show", "--active"],
                capture_output=True, text=True, timeout=5
            )
            
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                parts = line.split(':')
                if len(parts) >= 3 and parts[2] == "802-11-wireless":
                    # Get signal strength for active connection
                    signal = self._get_active_signal_strength()
                    return NetworkConnection(
                        ssid=parts[0],
                        signal_strength=signal,
                        connected=True,
                        known=True
                    )
        except Exception as e:
            print(f"Error getting active connection: {e}")
        return None
        
    def _get_active_signal_strength(self) -> int:
        """Get signal strength of active connection."""
        try:
            result = subprocess.run(
                ["nmcli", "-t", "-f", "SIGNAL", "device", "wifi", "list", "--rescan", "no"],
                capture_output=True, text=True, timeout=5
            )
            lines = result.stdout.strip().split('\n')
            if lines and lines[0]:
                return int(lines[0])
        except Exception:
            pass
        return 0

    def scan_wifi_networks_simple(self) -> List[NetworkConnection]:
        """Simple WiFi scan using nmcli only."""
        networks = []
        
        try:
            # Trigger rescan
            subprocess.run(
                ["nmcli", "device", "wifi", "rescan"],
                capture_output=True, timeout=10
            )
            
            # Get scan results
            result = subprocess.run(
                ["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY,IN-USE", "device", "wifi", "list"],
                capture_output=True, text=True, timeout=10
            )
            
            # Get known connections
            known_connections = self._get_known_connections()
            
            seen_ssids = set()
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                    
                parts = line.split(':')
                if len(parts) >= 4:
                    ssid = parts[0].strip()
                    if not ssid or ssid in seen_ssids:
                        continue
                        
                    seen_ssids.add(ssid)
                    
                    try:
                        signal = int(parts[1]) if parts[1] else 0
                    except ValueError:
                        signal = 0
                        
                    security = parts[2] if parts[2] else ""
                    connected = "*" in parts[3]
                    known = ssid in known_connections
                    
                    network = NetworkConnection(
                        ssid=ssid,
                        signal_strength=signal,
                        security=security,
                        connected=connected,
                        known=known
                    )
                    networks.append(network)
        
        except Exception as e:
            print(f"WiFi scan failed: {e}")
            
        # Sort by signal strength (connected first, then by signal)
        networks.sort(key=lambda x: (not x.connected, -x.signal_strength))
        return networks
        
    def _get_known_connections(self) -> set:
        """Get set of known/saved connection SSIDs."""
        known = set()
        try:
            result = subprocess.run(
                ["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"],
                capture_output=True, text=True, timeout=5
            )
            
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                parts = line.split(':')
                if len(parts) >= 2 and parts[1] == "802-11-wireless":
                    known.add(parts[0])
                    
        except Exception:
            pass
        return known
    
    def connect_to_network(self, ssid: str, password: str = "") -> bool:
        """Connect to a WiFi network."""
        try:
            if password:
                result = subprocess.run(
                    ["nmcli", "device", "wifi", "connect", ssid, "password", password],
                    capture_output=True, text=True, timeout=30
                )
            else:
                result = subprocess.run(
                    ["nmcli", "device", "wifi", "connect", ssid],
                    capture_output=True, text=True, timeout=30
                )
            return result.returncode == 0
        except Exception:
            return False
            
    def disconnect_active(self) -> bool:
        """Disconnect from active WiFi connection."""
        try:
            active = self.get_active_connection()
            if active:
                result = subprocess.run(
                    ["nmcli", "connection", "down", active.ssid],
                    capture_output=True, text=True, timeout=10
                )
                return result.returncode == 0
        except Exception:
            pass
        return False
        
    def forget_network(self, ssid: str) -> bool:
        """Forget/delete a saved network connection."""
        try:
            result = subprocess.run(
                ["nmcli", "connection", "delete", ssid],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False


class NetworkPopup(AppWindow):
    """Main network management popup."""
    
    def __init__(self, app, **kwargs):
        print("DEBUG: NetworkPopup.__init__ started")
        window_tag = kwargs.pop('window_tag', 'network')
        
        super().__init__(
            app=app,
            title="Network Manager",
            window_tag=window_tag,
            width=380,
            height=520,
            close_on_focus_loss=True,
            **kwargs
        )
        print("DEBUG: AppWindow initialized")
        
        # Create NetworkManager
        self.nm = NetworkManager()
        self.current_scan_thread = None
        self.available_networks = []
        self.scanning_active = False
        
        # Set up UI
        self.setup_ui()
        
        # Refresh status but don't auto-scan
        self.refresh_status_only()
        print("DEBUG: NetworkPopup.__init__ complete")
        
    def setup_ui(self):
        """Set up the UI components."""
        # WiFi power control
        wifi_enabled = self.nm.get_wifi_enabled() if self.nm else False
        
        self.wifi_toggle = ToggleRow(
            icon="󰤨",
            title="WiFi",
            subtitle="Enable or disable WiFi radio",
            initial_state=wifi_enabled,
            callback=self.on_wifi_toggle
        )
        self.main_box.append(self.wifi_toggle)
        self.main_box.append(Gtk.Separator())
        
        # Current connection info
        status_label = Gtk.Label(label="Connection Status", xalign=0)
        status_label.add_css_class("title-label")
        self.main_box.append(status_label)
        
        self.connection_info = Gtk.Label(label="Checking...", xalign=0)
        self.connection_info.add_css_class("subtitle-label")
        self.main_box.append(self.connection_info)
        
        self.main_box.append(Gtk.Separator())
        
        # Control buttons
        self.scan_button = ButtonRow()
        self.scan_btn = self.scan_button.add_button(
            "Scan Networks",
            callback=self.on_scan_clicked,
            icon="󰑐"
        )
        self.main_box.append(self.scan_button)
        
        # Disconnect button
        self.disconnect_button = ButtonRow()
        self.disconnect_btn = self.disconnect_button.add_button(
            "Disconnect",
            callback=self.on_disconnect_clicked,
            icon="󰅖"
        )
        self.main_box.append(self.disconnect_button)
        
        # Scan progress
        self.loading_widget = LoadingWidget(
            text="Click 'Scan Networks' to find available networks",
            show_spinner=False
        )
        self.main_box.append(self.loading_widget)
        
        self.main_box.append(Gtk.Separator())
        
        # Available networks
        networks_label = Gtk.Label(label="Available Networks", xalign=0)
        networks_label.add_css_class("title-label")
        self.main_box.append(networks_label)
        
        self.networks_list = ListWidget(height=200)
        self.main_box.append(self.networks_list)
        
        # Bottom buttons
        self.main_box.append(Gtk.Separator())
        bottom_buttons = ButtonRow()
        
        # Advanced settings button
        bottom_buttons.add_button(
            "Advanced",
            callback=self.open_advanced_settings,
            icon="󰒓"
        )
        
        # Close button
        bottom_buttons.add_button(
            "Close", 
            callback=lambda btn: self.close(), 
            icon="󰅖"
        )
        
        self.main_box.append(bottom_buttons)
        
    def refresh_status_only(self):
        """Refresh connection status without auto-scanning."""
        if not self.nm:
            self.connection_info.set_text("NetworkManager not available")
            self.disconnect_btn.set_sensitive(False)
            return
            
        if self.nm.get_airplane_mode():
            self.connection_info.set_text("Airplane mode enabled")
            self.disconnect_btn.set_sensitive(False)
            return
            
        if not self.nm.get_wifi_enabled():
            self.connection_info.set_text("WiFi disabled")
            self.disconnect_btn.set_sensitive(False)
            return
            
        # Update connection status
        active = self.nm.get_active_connection()
        if active:
            self.connection_info.set_text(f"Connected to {active.ssid} ({active.signal_strength}%)")
            self.disconnect_btn.set_sensitive(True)
        else:
            self.connection_info.set_text("Not connected")
            self.disconnect_btn.set_sensitive(False)
        
    def on_wifi_toggle(self, switch, state):
        """Handle WiFi power toggle."""
        if not self.nm:
            switch.set_active(not state)
            return
            
        if self.nm.set_wifi_enabled(state):
            status = "enabled" if state else "disabled"
            print(f"WiFi {status}")
            self.scan_btn.set_sensitive(state)
            
            if state:
                self.refresh_status_only()
            else:
                self.networks_list.clear_items()
                self.connection_info.set_text("WiFi disabled")
        else:
            print("Failed to change WiFi state")
            switch.set_active(not state)
            
    def on_scan_clicked(self, button):
        """Handle scan button clicks."""
        if self.scanning_active:
            return
            
        if not self.nm or not self.nm.get_wifi_enabled():
            return
            
        # Start scan
        self.scanning_active = True
        self.scan_btn.set_label("Scanning...")
        self.scan_btn.set_sensitive(False)
        self.loading_widget.set_spinning(True)
        self.loading_widget.set_text("Scanning for networks...")
        
        # Use simple scan
        self.current_scan_thread = run_async(
            target_func=self.nm.scan_wifi_networks_simple,
            success_callback=self.on_scan_complete,
            error_callback=self.on_scan_error,
            thread_name="wifi_scan"
        )
        
    def on_scan_complete(self, networks):
        """Handle scan completion."""
        self.current_scan_thread = None
        self.scanning_active = False
        self.scan_btn.set_label("Scan Networks")
        self.scan_btn.set_sensitive(True)
        self.loading_widget.set_spinning(False)
        
        self.available_networks = networks
        self.update_networks_list()
        self.loading_widget.set_text(f"Found {len(networks)} networks")
        
    def on_scan_error(self, error):
        """Handle scan errors."""
        self.current_scan_thread = None
        self.scanning_active = False
        self.scan_btn.set_label("Scan Networks")
        self.scan_btn.set_sensitive(True)
        self.loading_widget.set_spinning(False)
        self.loading_widget.set_text(f"Scan error: {error}")
        
    def on_disconnect_clicked(self, button):
        """Handle disconnect button click."""
        if not self.nm:
            return
            
        self.loading_widget.set_spinning(True)
        self.loading_widget.set_text("Disconnecting...")
        
        def disconnect_worker():
            return self.nm.disconnect_active()
            
        def on_disconnect_success(success):
            self.loading_widget.set_spinning(False)
            if success:
                self.show_notification("Disconnected from WiFi")
                self.refresh_status_only()
                self.loading_widget.set_text("Disconnected")
            else:
                self.show_notification("Failed to disconnect")
                self.loading_widget.set_text("Disconnect failed")
                
        def on_disconnect_error(error):
            self.loading_widget.set_spinning(False)
            self.show_notification(f"Disconnect error: {error}")
            self.loading_widget.set_text("Disconnect failed")
            
        run_async(
            target_func=disconnect_worker,
            success_callback=on_disconnect_success,
            error_callback=on_disconnect_error,
            thread_name="wifi_disconnect"
        )
        
    def update_networks_list(self):
        """Update the networks list display."""
        self.networks_list.clear_items()
        
        if not self.available_networks:
            self.networks_list.add_item("ℹ️", "No networks found", "Try scanning again")
            return
            
        for network in self.available_networks:
            subtitle = f"Signal: {network.get_signal_bars()} ({network.signal_strength}%)"
            if network.security:
                subtitle += f" • {network.security}"
            if network.connected:
                subtitle += " • Connected"
            elif network.known:
                subtitle += " • Saved"
                
            self.networks_list.add_item(
                network.get_icon(),
                network.ssid,
                subtitle,
                callback=self.on_network_clicked,
                right_click_callback=self.on_network_right_clicked if network.known else None,
                data=network
            )
            
    def on_network_clicked(self, row, network: NetworkConnection):
        """Handle network selection (connect)."""
        if network.connected:
            return  # Already connected
            
        # Show connection progress
        self.loading_widget.set_spinning(True)
        self.loading_widget.set_text(f"Connecting to {network.ssid}...")
        
        def connect_worker():
            if network.known:
                # Try connecting without password first
                return self.nm.connect_to_network(network.ssid)
            else:
                # New network - for now try open connection
                # TODO: Implement password dialog for secured networks
                if not network.security:
                    return self.nm.connect_to_network(network.ssid)
                else:
                    return False  # Skip password networks for now
                
        def on_connect_success(success):
            self.loading_widget.set_spinning(False)
            if success:
                self.show_notification(f"Connected to {network.ssid}")
                self.refresh_status_only()
                self.loading_widget.set_text("Connected successfully")
            else:
                self.show_notification(f"Failed to connect to {network.ssid}")
                self.loading_widget.set_text("Connection failed")
                
        def on_connect_error(error):
            self.loading_widget.set_spinning(False)
            self.show_notification(f"Connection error: {error}")
            self.loading_widget.set_text("Connection failed")
            
        run_async(
            target_func=connect_worker,
            success_callback=on_connect_success,
            error_callback=on_connect_error,
            thread_name="wifi_connect"
        )
        
    def on_network_right_clicked(self, row, network: NetworkConnection):
        """Handle right-click on network (forget)."""
        if not network.known:
            return
            
        # Show forget progress
        self.loading_widget.set_spinning(True)
        self.loading_widget.set_text(f"Forgetting {network.ssid}...")
        
        def forget_worker():
            return self.nm.forget_network(network.ssid)
            
        def on_forget_success(success):
            self.loading_widget.set_spinning(False)
            if success:
                self.show_notification(f"Forgot {network.ssid}")
                self.refresh_status_only()
                # Trigger a new scan to update the list
                self.on_scan_clicked(None)
                self.loading_widget.set_text("Network forgotten")
            else:
                self.show_notification(f"Failed to forget {network.ssid}")
                self.loading_widget.set_text("Forget failed")
                
        def on_forget_error(error):
            self.loading_widget.set_spinning(False)
            self.show_notification(f"Forget error: {error}")
            self.loading_widget.set_text("Forget failed")
            
        run_async(
            target_func=forget_worker,
            success_callback=on_forget_success,
            error_callback=on_forget_error,
            thread_name="wifi_forget"
        )
        
    def show_notification(self, message: str):
        """Show system notification."""
        try:
            subprocess.run(
                ["notify-send", "Network", message],
                capture_output=True,
                timeout=5
            )
        except Exception:
            print(f"Notification: {message}")
            
    def open_advanced_settings(self, button):
        """Open advanced network settings GUI."""
        # Try different network manager GUIs in order of preference
        network_managers = [
            ("nm-connection-editor", "NetworkManager Connection Editor"),
            ("gnome-control-center", "GNOME Control Center"),
            (["gnome-control-center", "network"], "GNOME Network Settings"),
            ("systemsettings5", "KDE System Settings"),
            (["systemsettings5", "kcm_networkmanagement"], "KDE Network Settings")
        ]
        
        for cmd, name in network_managers:
            try:
                if isinstance(cmd, list):
                    subprocess.Popen(cmd)
                else:
                    subprocess.Popen([cmd])
                self.show_notification(f"Opening {name}")
                return
            except FileNotFoundError:
                continue
            except Exception as e:
                print(f"Failed to open {name}: {e}")
                continue
        
        # If all else fails, show notification
        self.show_notification("No network manager GUI found. Install nm-connection-editor or gnome-control-center.")


if __name__ == "__main__":
    print("DEBUG: Starting fixed network popup")
    try:
        app = QuickApp(
            application_id="com.myui.network-fixed",
            window_class=NetworkPopup
        )
        print("DEBUG: QuickApp created, running...")
        app.run()
    except Exception as e:
        print(f"DEBUG: Error starting network popup: {e}")
        import traceback
        traceback.print_exc()