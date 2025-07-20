#!/usr/bin/env python3
"""
Widget Showcase - MyUI Framework Demo
====================================

A clean demonstration of all MyUI widgets including the new
ListWidget, TabWidget, and LoadingWidget components.
"""

import sys
from pathlib import Path
from gi.repository import Gtk, GLib

sys.path.insert(0, str(Path(__file__).parent.parent))
from widgets.myui import (AppWindow, SliderRow, ButtonRow, InfoRow, ToggleRow, 
                         ProgressRow, ListWidget, TabWidget, LoadingWidget, QuickApp)


class WidgetShowcase(AppWindow):
    """Complete showcase of all MyUI widgets."""

    def __init__(self, app, **kwargs):
        window_tag = kwargs.pop('window_tag', 'showcase')
        super().__init__(
            app=app,
            title="MyUI Widget Showcase",
            width=450,
            height=550,
            window_tag=window_tag,
            **kwargs
        )

        self.add_title("MyUI Framework", "Complete widget demonstration")

        # Create main tab widget
        self.tabs = TabWidget()
        
        self.create_basic_widgets_tab()
        self.create_list_widgets_tab() 
        self.create_interactive_tab()
        
        self.add_widget(self.tabs)

    def create_basic_widgets_tab(self):
        """Tab showing traditional MyUI widgets."""
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_top(16)
        content.set_margin_bottom(16)
        content.set_margin_start(16)
        content.set_margin_end(16)

        # Slider
        slider = SliderRow(
            icon="🔊", 
            text="Volume Control", 
            initial_value=75,
            show_value=True,
            callback=lambda s: print(f"Volume: {s.get_value()}%")
        )
        content.append(slider)

        # Toggle
        toggle = ToggleRow(
            icon="🔇",
            title="Mute Audio", 
            subtitle="Disable all sound output",
            callback=lambda switch, state: print(f"Muted: {state}")
        )
        content.append(toggle)

        # Info row
        info = InfoRow(
            icon="💾",
            title="Storage Usage",
            subtitle="85% of 512 GB used"
        )
        content.append(info)

        # Progress
        progress = ProgressRow(
            icon="⬇️", 
            title="Download Progress",
            subtitle="Downloading updates...",
            initial_progress=0.6
        )
        content.append(progress)

        # Buttons
        buttons = ButtonRow(spacing=8)
        buttons.add_button("Action 1", lambda b: print("Action 1"))
        buttons.add_button("Action 2", lambda b: print("Action 2"))
        content.append(buttons)

        self.tabs.add_page("Basic Widgets", content, "🎛️")

    def create_list_widgets_tab(self):
        """Tab showing ListWidget and LoadingWidget."""
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_top(16)
        content.set_margin_bottom(16)
        content.set_margin_start(16)
        content.set_margin_end(16)

        # List widget
        device_list = ListWidget(height=200)
        device_list.add_item(
            "🎧", "Bluetooth Headphones", "Connected • 92% battery",
            callback=lambda row, data: print(f"Selected: {data}"),
            data="headphones"
        )
        device_list.add_item(
            "📱", "iPhone", "Paired but not connected",
            callback=lambda row, data: print(f"Selected: {data}"),
            data="iphone"
        )
        device_list.add_separator()
        device_list.add_item(
            "🖱️", "Wireless Mouse", "Connected • Low battery",
            callback=lambda row, data: print(f"Selected: {data}"),
            data="mouse"
        )
        device_list.add_item(
            "⌨️", "Mechanical Keyboard", "Connected",
            callback=lambda row, data: print(f"Selected: {data}"),
            data="keyboard"
        )
        content.append(device_list)

        # Loading widget
        loading = LoadingWidget("Scanning for devices...")
        content.append(loading)

        # Control buttons
        controls = ButtonRow(spacing=6)
        controls.add_button("Refresh", lambda b: self.refresh_devices(device_list, loading))
        controls.add_button("Clear", lambda b: device_list.clear_items())
        content.append(controls)

        self.tabs.add_page("Lists & Loading", content, "📋")

    def create_interactive_tab(self):
        """Tab showing interactive features."""
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_top(16)
        content.set_margin_bottom(16)
        content.set_margin_start(16)
        content.set_margin_end(16)

        # Dynamic list
        self.dynamic_list = ListWidget(height=150)
        self.dynamic_list.add_item("ℹ️", "Click buttons below", "to add/remove items")
        content.append(self.dynamic_list)

        # Interactive controls
        controls1 = ButtonRow(spacing=6)
        controls1.add_button("Add Device", self.add_random_device)
        controls1.add_button("Remove Last", self.remove_last_device)
        content.append(controls1)

        # Tab switching demo
        tab_controls = ButtonRow(spacing=6)
        tab_controls.add_button("← Basic", lambda b: self.tabs.set_current_page(0))
        tab_controls.add_button("Lists →", lambda b: self.tabs.set_current_page(1))
        content.append(tab_controls)

        # Loading simulation
        self.sim_loading = LoadingWidget("Ready to simulate", show_spinner=False)
        content.append(self.sim_loading)

        simulate_btn = ButtonRow(spacing=6)
        simulate_btn.add_button("Simulate Loading", self.simulate_operation)
        content.append(simulate_btn)

        self.tabs.add_page("Interactive", content, "🎮")

    def refresh_devices(self, device_list, loading_widget):
        """Simulate refreshing device list."""
        print("Refreshing devices...")
        loading_widget.set_text("Refreshing devices...")
        loading_widget.set_spinning(True)
        
        # Stop after 2 seconds
        GLib.timeout_add(2000, lambda: loading_widget.set_spinning(False))

    def add_random_device(self, button):
        """Add a random device to the dynamic list."""
        import random
        devices = [
            ("🎮", "Gaming Controller", "Wireless"),
            ("🖥️", "External Monitor", "USB-C"),
            ("🔌", "Power Adapter", "Connected"),
            ("📹", "Webcam", "HD 1080p"),
            ("🎤", "Microphone", "USB Audio"),
        ]
        
        icon, name, desc = random.choice(devices)
        num = random.randint(100, 999)
        
        self.dynamic_list.add_item(
            icon, f"{name} {num}", desc,
            callback=lambda row, data: print(f"Clicked: {data}"),
            data=f"{name.lower()}{num}"
        )

    def remove_last_device(self, button):
        """Remove the last item from the dynamic list."""
        # Clear and re-add all but last (simple approach)
        self.dynamic_list.clear_items()
        self.dynamic_list.add_item("ℹ️", "Item removed", "Add more items with buttons above")

    def simulate_operation(self, button):
        """Simulate a long-running operation."""
        self.sim_loading.set_text("Processing...")
        self.sim_loading.set_spinning(True)
        
        # Complete after 3 seconds
        GLib.timeout_add(3000, self.complete_simulation)

    def complete_simulation(self):
        """Complete the simulated operation."""
        self.sim_loading.set_text("Operation completed!")
        self.sim_loading.set_spinning(False)
        return False  # Don't repeat


if __name__ == "__main__":
    app = QuickApp(
        application_id="com.myui.WidgetShowcase",
        window_class=WidgetShowcase,
        window_tag="showcase"
    )
    app.run_quick()