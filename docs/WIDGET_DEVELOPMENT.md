# MyUI Widget Development Guide

This guide covers everything you need to know about creating custom widgets and popups using the MyUI toolkit.

## Table of Contents

1. [MyUI Architecture Overview](#myui-architecture-overview)
2. [Available Widget Components](#available-widget-components)
3. [Creating Your First Custom Widget](#creating-your-first-custom-widget)
4. [Building Custom Popups](#building-custom-popups)
5. [Extending Existing Widgets](#extending-existing-widgets)
6. [Adding Popups to the Manager](#adding-popups-to-the-manager)
7. [Styling and Theming](#styling-and-theming)
8. [Best Practices](#best-practices)
9. [Advanced Patterns](#advanced-patterns)

## MyUI Architecture Overview

MyUI is built on top of GTK4 and libadwaita, providing a simplified API for creating consistent popup interfaces.

### Core Components

```
widgets/myui/
├── __init__.py              # Easy imports and exports
├── base_window.py           # AppWindow (base popup class) + QuickApp (launcher)
├── theming.py              # Automatic CSS loading and theme management
├── async_utils.py          # Threading utilities for non-blocking operations
└── components/widgets.py    # All reusable widget implementations
```

### Key Classes

- **`AppWindow`**: Base class for all popup windows
- **`QuickApp`**: Application launcher for standalone popups
- **Widget Classes**: Pre-built components (SliderRow, ButtonRow, etc.)
- **Theming System**: Automatic Material Design 3 integration

## Available Widget Components

### Basic Widgets

| Widget | Purpose | Key Features |
|--------|---------|--------------|
| `SliderRow` | Numeric input with slider | Icon, label, value display, callbacks |
| `ButtonRow` | Horizontal button groups | Multiple buttons, icons, custom callbacks |
| `InfoRow` | Display information | Icon, title, subtitle, clean layout |
| `ToggleRow` | Boolean input with switch | Based on InfoRow + toggle switch |
| `ProgressRow` | Progress indication | Based on InfoRow + progress bar |

### Advanced Widgets

| Widget | Purpose | Key Features |
|--------|---------|--------------|
| `ListWidget` | Scrollable content lists | Dynamic items, selection, custom renderers |
| `TabWidget` | Multi-panel interfaces | Tab switching, lazy loading |
| `LoadingWidget` | Async operation feedback | Spinner animation, status text |

### Usage Example

```python
from widgets.myui import SliderRow, ButtonRow, ToggleRow

# Create a slider with callback
volume_slider = SliderRow(
    icon="🔊",
    title="Volume",
    subtitle="Master audio level",
    initial_value=75,
    min_value=0,
    max_value=100,
    callback=self.on_volume_change
)

# Create a button row
controls = ButtonRow()
controls.add_button("Mute", self.toggle_mute, icon="🔇")
controls.add_button("Max", lambda _: volume_slider.set_value(100), icon="📢")

# Create a toggle switch
dark_mode = ToggleRow(
    icon="🌙",
    title="Dark Mode",
    subtitle="Use dark theme variant",
    initial_state=True,
    callback=self.on_theme_toggle
)
```

## Creating Your First Custom Widget

Let's create a custom color picker widget step by step:

### Step 1: Basic Widget Structure

```python
# widgets/myui/components/widgets.py

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk

class ColorPickerRow(Gtk.Box):
    """Custom color picker widget with preview and callback."""
    
    def __init__(self, icon="🎨", title="Color", initial_color="#3584e4", callback=None):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.add_css_class("widget-row")
        
        self.callback = callback
        self.current_color = initial_color
        
        # Icon
        self.icon_label = Gtk.Label(label=icon)
        self.icon_label.add_css_class("icon-label")
        self.append(self.icon_label)
        
        # Title
        self.title_label = Gtk.Label(label=title)
        self.title_label.add_css_class("title-label")
        self.title_label.set_hexpand(True)
        self.title_label.set_halign(Gtk.Align.START)
        self.append(self.title_label)
        
        # Color preview button
        self.color_button = Gtk.Button()
        self.color_button.set_size_request(40, 40)
        self.color_button.add_css_class("color-preview")
        self.color_button.connect("clicked", self.on_color_button_clicked)
        self.update_color_preview()
        self.append(self.color_button)
    
    def update_color_preview(self):
        """Update the color preview button."""
        css = f"""
        .color-preview {{
            background-color: {self.current_color};
            border-radius: 6px;
            border: 2px solid alpha(@outline_variant, 0.5);
        }}
        """
        # Apply CSS (simplified - in practice you'd use the theming system)
        
    def on_color_button_clicked(self, button):
        """Open color chooser dialog."""
        dialog = Gtk.ColorChooserDialog(title="Choose Color")
        dialog.set_modal(True)
        dialog.set_transient_for(self.get_root())
        
        # Set initial color
        rgba = Gdk.RGBA()
        rgba.parse(self.current_color)
        dialog.set_rgba(rgba)
        
        dialog.connect("response", self.on_color_dialog_response)
        dialog.present()
    
    def on_color_dialog_response(self, dialog, response):
        """Handle color dialog response."""
        if response == Gtk.ResponseType.OK:
            rgba = dialog.get_rgba()
            self.current_color = f"#{int(rgba.red*255):02x}{int(rgba.green*255):02x}{int(rgba.blue*255):02x}"
            self.update_color_preview()
            
            if self.callback:
                self.callback(self.current_color)
        
        dialog.destroy()
    
    def get_color(self):
        """Get current color value."""
        return self.current_color
    
    def set_color(self, color):
        """Set color programmatically."""
        self.current_color = color
        self.update_color_preview()
```

### Step 2: Export Your Widget

Add your new widget to the exports in `widgets/myui/__init__.py`:

```python
# widgets/myui/__init__.py

from .components.widgets import (SliderRow, ButtonRow, InfoRow, ToggleRow, 
                                ProgressRow, ListWidget, TabWidget, 
                                LoadingWidget, ColorPickerRow)  # Add here

__all__ = ['AppWindow', 'QuickApp', 'SliderRow', 'ButtonRow', 'InfoRow', 
           'ToggleRow', 'ProgressRow', 'ListWidget', 'TabWidget', 
           'LoadingWidget', 'ColorPickerRow']  # Add here
```

### Step 3: Use Your Custom Widget

```python
from widgets.myui import AppWindow, ColorPickerRow, QuickApp

class ThemeCustomizer(AppWindow):
    def __init__(self, app, **kwargs):
        super().__init__(
            app=app,
            title="Theme Customizer",
            width=400,
            height=300,
            **kwargs
        )
        
        # Add color pickers
        primary_color = ColorPickerRow(
            icon="🎨",
            title="Primary Color",
            initial_color="#3584e4",
            callback=self.on_primary_color_changed
        )
        self.add_widget(primary_color)
        
        accent_color = ColorPickerRow(
            icon="✨",
            title="Accent Color", 
            initial_color="#e66100",
            callback=self.on_accent_color_changed
        )
        self.add_widget(accent_color)
    
    def on_primary_color_changed(self, color):
        print(f"Primary color changed to: {color}")
    
    def on_accent_color_changed(self, color):
        print(f"Accent color changed to: {color}")

if __name__ == "__main__":
    app = QuickApp("com.example.ThemeCustomizer", ThemeCustomizer)
    app.run()
```

## Building Custom Popups

### Basic Popup Template

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from widgets.myui import AppWindow, SliderRow, ButtonRow, ToggleRow
from widgets.myui.base_window import QuickApp

class MyCustomPopup(AppWindow):
    """Template for custom popup implementation."""
    
    def __init__(self, app, **kwargs):
        # Extract window_tag and pass other kwargs to parent
        window_tag = kwargs.pop('window_tag', 'mycustom')
        super().__init__(
            app=app,
            title="My Custom Popup",
            width=350,
            height=250,
            window_tag=window_tag,
            close_on_focus_loss=True,  # Typical popup behavior
            **kwargs
        )
        
        # Add title and subtitle
        self.add_title("Custom Settings", "Configure your custom options")
        
        # Add your widgets here
        self.setup_widgets()
    
    def setup_widgets(self):
        """Set up the popup interface."""
        # Example slider
        sensitivity = SliderRow(
            icon="⚡",
            title="Sensitivity",
            subtitle="Adjust response sensitivity",
            initial_value=50,
            callback=self.on_sensitivity_change
        )
        self.add_widget(sensitivity)
        
        # Example toggle
        auto_mode = ToggleRow(
            icon="🤖",
            title="Auto Mode",
            subtitle="Enable automatic adjustments",
            initial_state=False,
            callback=self.on_auto_toggle
        )
        self.add_widget(auto_mode)
        
        # Example buttons
        self.add_separator()
        actions = ButtonRow()
        actions.add_button("Reset", self.reset_settings, icon="🔄")
        actions.add_button("Apply", self.apply_settings, icon="✓")
        self.add_widget(actions)
    
    def on_sensitivity_change(self, slider):
        """Handle sensitivity changes."""
        value = int(slider.get_value())
        print(f"Sensitivity: {value}%")
    
    def on_auto_toggle(self, switch, state):
        """Handle auto mode toggle."""
        print(f"Auto mode: {'enabled' if state else 'disabled'}")
    
    def reset_settings(self, button):
        """Reset all settings to defaults."""
        print("Resetting settings...")
    
    def apply_settings(self, button):
        """Apply current settings."""
        print("Applying settings...")
        self.close()  # Close popup after applying

if __name__ == "__main__":
    app = QuickApp("com.example.MyCustomPopup", MyCustomPopup)
    app.run()
```

## Extending Existing Widgets

### Method 1: Inheritance

```python
class VolumeSlider(SliderRow):
    """Enhanced slider with volume-specific features."""
    
    def __init__(self, **kwargs):
        # Set volume-specific defaults
        kwargs.setdefault('icon', '🔊')
        kwargs.setdefault('title', 'Volume')
        kwargs.setdefault('min_value', 0)
        kwargs.setdefault('max_value', 100)
        kwargs.setdefault('show_value', True)
        
        super().__init__(**kwargs)
        
        # Add volume-specific styling
        self.add_css_class("volume-slider")
        
        # Connect to volume-specific callback
        self.original_callback = self.callback
        self.callback = self.volume_callback
    
    def volume_callback(self, slider):
        """Volume-specific callback with additional features."""
        value = int(slider.get_value())
        
        # Update icon based on volume level
        if value == 0:
            self.icon_label.set_text("🔇")
        elif value < 50:
            self.icon_label.set_text("🔉")
        else:
            self.icon_label.set_text("🔊")
        
        # Call original callback if provided
        if self.original_callback:
            self.original_callback(slider)
```

### Method 2: Composition

```python
class NetworkStatus(Gtk.Box):
    """Composite widget combining InfoRow with status indicator."""
    
    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        # Main info row
        self.info_row = InfoRow(
            icon="🌐",
            title="Network Status",
            subtitle="Checking connection..."
        )
        self.append(self.info_row)
        
        # Status indicator
        self.status_bar = Gtk.ProgressBar()
        self.status_bar.set_pulse_step(0.1)
        self.status_bar.add_css_class("network-status-bar")
        self.append(self.status_bar)
        
        # Start status checking
        self.check_network_status()
    
    def check_network_status(self):
        """Check network connectivity."""
        # Implementation here
        pass
    
    def update_status(self, connected, signal_strength=None):
        """Update the network status display."""
        if connected:
            self.info_row.set_subtitle(f"Connected • Signal: {signal_strength}%")
            self.status_bar.set_fraction(signal_strength / 100 if signal_strength else 1.0)
        else:
            self.info_row.set_subtitle("Disconnected")
            self.status_bar.set_fraction(0)
```

## Adding Popups to the Manager

### Step 1: Create Your Popup

Create your popup file in the `popups/` directory:

```python
# popups/my_custom_popup.py
#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from widgets.myui import AppWindow, QuickApp
# ... your popup implementation
```

### Step 2: Add Import to Manager

Edit `manager.py` to import your popup:

```python
# manager.py

# Import all popup window classes
from popups.brightness_popup import BrightnessPopup
from popups.volume_popup import VolumePopup
from popups.my_custom_popup import MyCustomPopup  # Add this line
# ... other imports
```

### Step 3: Register in Popup Map

Add your popup to the `popup_map` dictionary:

```python
# manager.py - in the do_command_line method

popup_map = {
    "brightness": BrightnessPopup,
    "volume": VolumePopup,
    "battery": BatteryPopup,
    "bluetooth": BluetoothPopup,
    "network": NetworkPopup,
    "systeminfo": SystemInfoPopup,
    "showcase": WidgetShowcase,
    "mycustom": MyCustomPopup,  # Add this line
}
```

### Step 4: Update Available List

Update the error message for unknown popups:

```python
# manager.py - in the else clause

print("Available: brightness, volume, battery, systeminfo, bluetooth, network, showcase, mycustom")
```

### Step 5: Test Your Integration

```bash
# Via manager daemon
./manager.py mycustom

# Direct execution
python3 popups/my_custom_popup.py
```

## Styling and Theming

### CSS Class Conventions

MyUI uses consistent CSS classes for theming:

```css
/* Widget containers */
.widget-row          /* Base row styling */
.title-label         /* Widget titles */
.subtitle-label      /* Widget subtitles */
.icon-label          /* Widget icons */

/* Specific widgets */
.slider-row          /* SliderRow styling */
.button-row          /* ButtonRow styling */
.info-row            /* InfoRow styling */
.toggle-row          /* ToggleRow styling */
.progress-row        /* ProgressRow styling */

/* Interactive elements */
.widget-button       /* Buttons in ButtonRow */
.widget-slider       /* Sliders in SliderRow */
.widget-switch       /* Switches in ToggleRow */
.widget-progress     /* Progress bars */
```

### Adding Custom Styles

```python
class CustomWidget(Gtk.Box):
    def __init__(self):
        super().__init__()
        
        # Add standard MyUI classes
        self.add_css_class("widget-row")
        self.add_css_class("custom-widget")  # Your custom class
        
        # Style child elements
        label = Gtk.Label("Custom Text")
        label.add_css_class("title-label")
        label.add_css_class("custom-title")  # Additional styling
```

### Color Integration

MyUI automatically integrates with your Matugen colors:

```python
# Colors are automatically available from:
# @define-color primary
# @define-color surface
# @define-color on_surface
# etc.

# Use in your custom CSS:
"""
.my-custom-widget {
    background-color: @surface_container;
    color: @on_surface;
    border: 1px solid @outline_variant;
}
"""
```

## Best Practices

### 1. Follow Naming Conventions

```python
# Good: Descriptive, follows pattern
class NetworkSpeedMeter(InfoRow):
    pass

# Bad: Unclear, inconsistent
class NetSpd(Gtk.Box):
    pass
```

### 2. Use Composition Over Inheritance

```python
# Good: Flexible composition
class StatusPanel(Gtk.Box):
    def __init__(self):
        super().__init__()
        self.status_info = InfoRow(...)
        self.progress_bar = ProgressRow(...)
        self.control_buttons = ButtonRow(...)

# Less flexible: Deep inheritance
class StatusPanel(InfoRow):
    pass
```

### 3. Handle Errors Gracefully

```python
def update_network_status(self):
    try:
        status = get_network_status()
        self.update_display(status)
    except NetworkError as e:
        self.show_error(f"Network error: {e}")
        # Provide fallback or retry option
```

### 4. Use Async for Blocking Operations

```python
from widgets.myui import run_async

class NetworkPopup(AppWindow):
    def scan_networks(self):
        # Use async utilities for network scanning
        run_async(
            self.do_network_scan,
            on_complete=self.on_scan_complete,
            on_error=self.on_scan_error
        )
    
    def do_network_scan(self):
        # This runs in background thread
        return expensive_network_operation()
    
    def on_scan_complete(self, networks):
        # This runs on main thread
        self.update_network_list(networks)
```

### 5. Consistent Error Handling

```python
class MyPopup(AppWindow):
    def __init__(self, app, **kwargs):
        try:
            super().__init__(app=app, **kwargs)
            self.setup_widgets()
        except Exception as e:
            print(f"ERROR: Failed to initialize popup: {e}")
            # Provide minimal fallback interface
            self.setup_error_interface()
    
    def setup_error_interface(self):
        """Minimal interface when main setup fails."""
        error_info = InfoRow(
            icon="⚠️",
            title="Error",
            subtitle="Failed to load popup interface"
        )
        self.add_widget(error_info)
```

## Advanced Patterns

### Custom Theming Integration

```python
from widgets.myui.theming import apply_theme

class ThemedWidget(Gtk.Box):
    def __init__(self):
        super().__init__()
        
        # Apply MyUI theming
        apply_theme(self)
        
        # Add custom CSS
        self.add_custom_styling()
    
    def add_custom_styling(self):
        """Add widget-specific styling."""
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data("""
            .themed-widget {
                background: @surface_container;
                border-radius: 12px;
                padding: 12px;
                margin: 6px;
            }
        """.encode())
        
        # Apply to this widget
        style_context = self.get_style_context()
        style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.add_css_class("themed-widget")
```

### Dynamic Widget Creation

```python
class DynamicPopup(AppWindow):
    def __init__(self, app, config_items=None, **kwargs):
        super().__init__(app=app, **kwargs)
        
        # Create widgets based on configuration
        for item in config_items or []:
            widget = self.create_widget_from_config(item)
            if widget:
                self.add_widget(widget)
    
    def create_widget_from_config(self, config):
        """Create widget based on configuration dictionary."""
        widget_type = config.get('type')
        
        if widget_type == 'slider':
            return SliderRow(
                icon=config.get('icon', '⚙️'),
                title=config.get('title', 'Setting'),
                initial_value=config.get('value', 50),
                callback=lambda s: self.on_setting_change(config['key'], s.get_value())
            )
        elif widget_type == 'toggle':
            return ToggleRow(
                icon=config.get('icon', '🔧'),
                title=config.get('title', 'Option'),
                initial_state=config.get('enabled', False),
                callback=lambda s, state: self.on_setting_change(config['key'], state)
            )
        # Add more widget types as needed
        
        return None
    
    def on_setting_change(self, key, value):
        """Handle dynamic setting changes."""
        print(f"Setting {key} changed to {value}")
```

### State Management Pattern

```python
class StatefulPopup(AppWindow):
    def __init__(self, app, **kwargs):
        super().__init__(app=app, **kwargs)
        
        # Initialize state
        self.state = {
            'volume': 50,
            'muted': False,
            'profile': 'balanced'
        }
        
        self.setup_widgets()
        self.load_state()
    
    def load_state(self):
        """Load state from persistent storage."""
        try:
            with open(self.get_state_file(), 'r') as f:
                self.state.update(json.load(f))
            self.update_widgets_from_state()
        except FileNotFoundError:
            pass  # Use defaults
    
    def save_state(self):
        """Save current state persistently."""
        with open(self.get_state_file(), 'w') as f:
            json.dump(self.state, f)
    
    def get_state_file(self):
        """Get path to state file."""
        return Path.home() / '.config' / 'myui-popups' / 'popup-state.json'
    
    def update_state(self, key, value):
        """Update state and save."""
        self.state[key] = value
        self.save_state()
        self.update_widgets_from_state()
```

---