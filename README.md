# MyUI Popups

A GTK4-based popup system for Waybar integration, featuring the custom **MyUI toolkit** for rapid UI development. Supports both direct execution and optional daemon architecture for enhanced performance.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![GTK4](https://img.shields.io/badge/GTK-4.0+-green.svg)](https://gtk.org/)

## ✨ Features

- **🚀 Dual Launch Methods**: Direct execution or optional manager daemon
- **🎨 Automatic Theming**: Seamless integration with Matugen color schemes  
- **🧩 Custom Toolkit**: MyUI widgets for rapid popup development
- **🔧 Waybar Ready**: Drop-in replacement for traditional menu scripts
- **📱 Modern Design**: Clean Material Design 3 aesthetic with libadwaita
- **🎯 Focus-Aware**: Smart popup behavior with auto-close on focus loss
- **⚡ Async Support**: Non-blocking operations for bluetooth scanning and network management

## 🏗️ Architecture

### Dual Launch System
- **Direct execution**: Run popup scripts directly for simple integration
- **Manager daemon**: Optional background service for instant launch (recommended for UWSM)
- **Hyprland integration**: Can be started via `exec-once` or systemd service

### Available Popups
- **`brightness_popup.py`** - Display brightness control with theme toggle
- **`volume_popup.py`** - Audio volume control with presets  
- **`battery_popup.py`** - Power management and battery info
- **`network_popup.py`** - WiFi management with async scanning
- **`bluetooth_popup.py`** - Bluetooth device management with real-time scanning
- **`system_info_popup.py`** - System information display
- **`widget_showcase.py`** - Demo of all MyUI components

### MyUI Widget Library
```
widgets/myui/
├── __init__.py              # Easy imports: AppWindow, QuickApp, all widgets
├── base_window.py           # AppWindow (base popup) + QuickApp (launcher)  
├── theming.py              # Auto CSS loading from colors.css + fallbacks
├── async_utils.py           # Threading and async operation utilities
└── components/widgets.py    # All widget implementations
```

## 🚀 Quick Start

### Installation

1. **Clone the repository**:
```bash
git clone https://github.com/givani30/myui-popups.git
cd myui-popups
```

2. **Install dependencies**:
```bash
# Arch Linux
sudo pacman -S python python-gobject gtk4 libadwaita

# Ubuntu/Debian  
sudo apt install python3 python3-gi gir1.2-gtk-4.0 gir1.2-adw-1
```

### Two Ways to Launch Popups

#### Method 1: Direct Execution (Simple)
```bash
# Run popups directly - good for basic Waybar integration
python3 popups/brightness_popup.py
python3 popups/volume_popup.py
python3 popups/network_popup.py
python3 popups/bluetooth_popup.py
python3 popups/battery_popup.py
```

#### Method 2: Manager Daemon (Advanced)
For faster launch times and better resource management:

**Option A: Systemd Service (UWSM)**
```bash
# Create service file
cat > ~/.config/systemd/user/myui-popups-manager.service << 'EOF'
[Unit]
Description=MyUI Popups Manager Daemon
After=graphical-session.target

[Service]
Type=simple
ExecStart=%h/.config/waybar_popups/manager.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF

# Enable and start
systemctl --user enable myui-popups-manager
systemctl --user start myui-popups-manager

# Launch popups via manager
./manager.py brightness
./manager.py volume
./manager.py network
```

**Option B: Hyprland exec-once**
```bash
# Add to your hyprland.conf
exec-once = ~/.config/waybar_popups/manager.py

# Then launch popups the same way
~/.config/waybar_popups/manager.py brightness
```

## 📋 Available Popups

| Popup | Description | Key Features |
|-------|-------------|--------------|
| **brightness** | Display control | Laptop + external monitor sliders, theme toggle |
| **volume** | Audio control | Master volume, mute toggle, preset buttons |
| **network** | WiFi management | Connection status, async scanning, advanced settings |
| **bluetooth** | Device management | Real-time scanning, pairing, connection control |
| **battery** | Power monitoring | Charge level, power profiles, system info |
| **systeminfo** | System information | Hardware details, resource usage |
| **showcase** | Component demo | All available MyUI widgets |

## 🧩 MyUI Widget System

### Available Widgets

- **`SliderRow`** - Icon + label + slider with value display
- **`ButtonRow`** - Horizontal button groups with icons  
- **`InfoRow`** - Information display with icon/title/subtitle
- **`ToggleRow`** - Info row with toggle switch
- **`ProgressRow`** - Info row with progress bar
- **`ListWidget`** - Scrollable lists for dynamic content
- **`TabWidget`** - Multi-tab interfaces
- **`LoadingWidget`** - Animated loading indicators

### Creating Custom Popups

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from widgets.myui import AppWindow, SliderRow, ButtonRow
from widgets.myui.base_window import QuickApp

class CustomPopup(AppWindow):
    def __init__(self, app, **kwargs):
        super().__init__(
            app=app,
            title="Custom Popup", 
            window_tag="custom-popup",
            width=350,
            height=200,
            **kwargs
        )
        
        # Add volume slider
        volume_slider = SliderRow(
            icon="🔊",
            title="Volume",
            initial_value=75,
            callback=self.on_volume_change
        )
        self.add_widget(volume_slider)
        
        # Add control buttons
        controls = ButtonRow()
        controls.add_button("Mute", self.toggle_mute, icon="🔇")
        controls.add_button("Max", lambda _: volume_slider.set_value(100), icon="📢")
        self.add_widget(controls)
    
    def on_volume_change(self, slider):
        value = int(slider.get_value())
        print(f"Setting volume to {value}%")
    
    def toggle_mute(self, button):
        print("Toggling mute")

if __name__ == "__main__":
    app = QuickApp("com.example.CustomPopup", CustomPopup)
    app.run()
```

### Adding Popups to Manager

To integrate a new popup with the manager daemon:

1. **Create your popup class** inheriting from `AppWindow`
2. **Add import** to `manager.py`:
   ```python
   from my_custom_popup import MyCustomPopup
   ```
3. **Add to popup_map** in `manager.py`:
   ```python
   popup_map = {
       "brightness": BrightnessPopup,
       "volume": VolumePopup,
       "mycustom": MyCustomPopup,  # Add your popup here
       # ... existing popups
   }
   ```
4. **Launch with**: `./manager.py mycustom`

## 🎨 Theming System

MyUI automatically integrates with your existing theme:

1. **Matugen Integration**: Reads `~/.config/waybar/colors.css`
2. **Local Override**: Falls back to local `colors.css`  
3. **Built-in Fallback**: Catppuccin-inspired default theme

### Color Variables
The system maps Material Design 3 colors to CSS variables:
- `@define-color primary` → Primary accent color
- `@define-color surface` → Background surfaces
- `@define-color on_surface` → Text colors
- `@define-color surface_container` → Widget backgrounds

## 🔧 Waybar Integration

### Method 1: Direct Execution
```json
{
  "modules-right": ["custom/brightness", "custom/volume", "custom/network"],
  
  "custom/brightness": {
    "format": "☀",
    "on-click": "~/.config/waybar_popups/popups/brightness_popup.py",
    "tooltip": false
  },
  "custom/volume": {
    "format": "🔊", 
    "on-click": "~/.config/waybar_popups/popups/volume_popup.py",
    "tooltip": false
  },
  "custom/network": {
    "format": "🌐",
    "on-click": "~/.config/waybar_popups/popups/network_popup.py", 
    "tooltip": false
  }
}
```

### Method 2: Manager Daemon
```json
{
  "modules-right": ["custom/brightness", "custom/volume", "custom/network"],
  
  "custom/brightness": {
    "format": "☀",
    "on-click": "~/.config/waybar_popups/manager.py brightness",
    "tooltip": false
  },
  "custom/volume": {
    "format": "🔊", 
    "on-click": "~/.config/waybar_popups/manager.py volume",
    "tooltip": false
  },
  "custom/network": {
    "format": "🌐",
    "on-click": "~/.config/waybar_popups/manager.py network", 
    "tooltip": false
  }
}
```

## 🛠️ Development

### Service Management (Daemon Mode)
```bash
# Restart after code changes
systemctl --user restart myui-popups-manager

# Check status and logs
systemctl --user status myui-popups-manager
journalctl --user -u myui-popups-manager -f
```

### Testing Widgets
```bash
python3 popups/widget_showcase.py    # Complete widget demo
python3 popups/brightness_popup.py   # Test individual popup
```

### Project Structure
```
myui-popups/
├── manager.py                    # Daemon manager (optional)
├── popups/                      # All popup implementations
│   ├── brightness_popup.py      # Display brightness control
│   ├── volume_popup.py          # Audio volume control  
│   ├── network_popup.py         # WiFi management
│   ├── bluetooth_popup.py       # Bluetooth device control
│   ├── battery_popup.py         # Power management
│   ├── system_info_popup.py     # System information
│   └── widget_showcase.py       # Widget demonstration
├── widgets/myui/                # MyUI toolkit
│   ├── __init__.py
│   ├── base_window.py           # AppWindow + QuickApp
│   ├── theming.py              # CSS theming system
│   ├── async_utils.py          # Threading utilities
│   └── components/widgets.py    # All widget classes
├── examples/                    # Additional examples
└── pyproject.toml              # Project metadata
```

## 📦 Dependencies

- **Python 3.8+** with PyGObject
- **GTK4 + libadwaita** for modern UI components  
- **PulseAudio** (for volume control)
- **NetworkManager** (for network popup)
- **Bluetooth** (for bluetooth popup)
- **systemd** (optional, for daemon service)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-widget`
3. Implement your changes with proper error handling
4. Test with `python3 widget_showcase.py`
5. Submit a pull request

### Widget Development Guidelines
- Inherit from appropriate GTK base classes
- Add CSS classes for consistent theming
- Use callback patterns for user interactions
- Export new widgets in `__init__.py`

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **GTK Team** - For the excellent GTK4 framework
- **GNOME libadwaita** - For modern design components
- **Waybar** - For the inspiration and integration target
- **Matugen** - For automated theme generation

---

**Made with ❤️ for the Linux desktop customization community**

*Transform your Waybar from basic to brilliant with MyUI Popups!*