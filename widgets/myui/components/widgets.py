"""
Widgets module for MyUI
======================

Contains reusable UI components that can be used across different popup windows.
All widgets automatically inherit theming from the theming module.
"""

from typing import Callable, Optional

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk


class SliderRow(Gtk.Box):
    """A self-contained widget for a labeled slider with icon."""
    
    def __init__(self, icon: str, text: str, initial_value: int = 50, 
                 min_val: int = 0, max_val: int = 100, step: int = 1,
                 callback: Optional[Callable] = None, show_value: bool = False,
                 on_release_callback: Optional[Callable] = None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        
        self.callback = callback
        self.on_release_callback = on_release_callback
        self.show_value = show_value
        
        # Label Box (icon + text + optional value)
        label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        # Icon
        icon_label = Gtk.Label(label=icon)
        icon_label.add_css_class("icon-label")
        label_box.append(icon_label)
        
        # Text
        text_label = Gtk.Label(label=text, xalign=0)
        text_label.set_hexpand(True)
        label_box.append(text_label)
        
        # Optional value display
        if show_value:
            self.value_label = Gtk.Label(label=f"{initial_value}%")
            self.value_label.add_css_class("subtitle-label")
            label_box.append(self.value_label)
        
        # Slider
        self.slider = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, min_val, max_val, step)
        self.slider.set_value(initial_value)
        self.slider.set_draw_value(False)
        self.slider.set_hexpand(True)
        self.slider.connect("value-changed", self._on_value_changed)
        
        # Connect button release for on_release_callback
        if self.on_release_callback:
            # Use a different approach - detect when dragging stops
            self.slider.connect("change-value", self._on_change_value)
            self._last_value = initial_value
            self._drag_timeout_id = None

        # Add to main widget box
        self.append(label_box)
        self.append(self.slider)

    def _on_value_changed(self, slider):
        """Internal callback that updates value display and calls user callback."""
        value = int(slider.get_value())
        
        # Update value display if enabled
        if self.show_value:
            self.value_label.set_text(f"{value}%")
        
        # Call user callback if provided (only if no on_release_callback)
        if self.callback and not self.on_release_callback:
            self.callback(slider)

    def _on_change_value(self, slider, scroll_type, value):
        """Called when slider value changes (for timeout-based release detection)."""
        from gi.repository import GLib
        
        # Cancel previous timeout if it exists
        if self._drag_timeout_id:
            GLib.source_remove(self._drag_timeout_id)
        
        # Set a new timeout - if no more changes happen in 200ms, consider it "released"
        self._drag_timeout_id = GLib.timeout_add(200, self._on_drag_timeout)
        return False  # Let the normal handling continue

    def _on_drag_timeout(self):
        """Called when dragging has stopped for a while."""
        current_value = int(self.slider.get_value())
        if current_value != self._last_value:
            print(f"DEBUG: Drag timeout triggered, calling on_release_callback with value {current_value}")
            if self.on_release_callback:
                self.on_release_callback(self.slider)
            self._last_value = current_value
        
        self._drag_timeout_id = None
        return False  # Don't repeat the timeout

    def get_value(self) -> int:
        """Get the current slider value."""
        return int(self.slider.get_value())
    
    def set_value(self, value: int):
        """Set the slider value programmatically."""
        self.slider.set_value(value)


class ButtonRow(Gtk.Box):
    """A row of buttons with optional icons."""
    
    def __init__(self, orientation=Gtk.Orientation.HORIZONTAL, spacing: int = 8):
        super().__init__(orientation=orientation, spacing=spacing)
        self.set_homogeneous(True)
    
    def add_button(self, text: str, callback: Optional[Callable] = None, 
                   icon: Optional[str] = None, destructive: bool = False) -> Gtk.Button:
        """Add a button to the row."""
        
        if icon:
            # Create button with icon and text
            button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            icon_label = Gtk.Label(label=icon)
            icon_label.add_css_class("icon-label")
            text_label = Gtk.Label(label=text)
            
            button_box.append(icon_label)
            button_box.append(text_label)
            
            button = Gtk.Button()
            button.set_child(button_box)
        else:
            # Simple text button
            button = Gtk.Button(label=text)
        
        if destructive:
            button.add_css_class("destructive")
            
        if callback:
            button.connect("clicked", callback)
            
        self.append(button)
        return button


class InfoRow(Gtk.Box):
    """A row displaying information with icon, title, and subtitle."""
    
    def __init__(self, icon: str, title: str, subtitle: str = "", 
                 action_widget: Optional[Gtk.Widget] = None):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.add_css_class("info-row")
        
        # Icon
        icon_label = Gtk.Label(label=icon)
        icon_label.add_css_class("icon-label")
        icon_label.set_valign(Gtk.Align.START)
        self.append(icon_label)
        
        # Text container
        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        text_box.set_hexpand(True)
        text_box.set_valign(Gtk.Align.CENTER)
        
        # Title
        title_label = Gtk.Label(label=title, xalign=0)
        title_label.add_css_class("title-label")
        text_box.append(title_label)
        
        # Subtitle (if provided)
        if subtitle:
            subtitle_label = Gtk.Label(label=subtitle, xalign=0)
            subtitle_label.add_css_class("subtitle-label")
            text_box.append(subtitle_label)
        
        self.append(text_box)
        
        # Action widget (button, switch, etc.)
        if action_widget:
            action_widget.set_valign(Gtk.Align.CENTER)
            self.append(action_widget)


class ToggleRow(InfoRow):
    """An info row with a toggle switch."""
    
    def __init__(self, icon: str, title: str, subtitle: str = "", 
                 initial_state: bool = False, callback: Optional[Callable] = None):
        
        # Create the switch
        self.switch = Gtk.Switch()
        self.switch.set_active(initial_state)
        
        if callback:
            self.switch.connect("state-set", callback)
        
        # Initialize with switch as action widget
        super().__init__(icon, title, subtitle, self.switch)
    
    def get_active(self) -> bool:
        """Get the switch state."""
        return self.switch.get_active()
    
    def set_active(self, active: bool):
        """Set the switch state."""
        self.switch.set_active(active)


class ProgressRow(InfoRow):
    """An info row with a progress bar."""
    
    def __init__(self, icon: str, title: str, subtitle: str = "", 
                 initial_progress: float = 0.0):
        
        # Create the progress bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_fraction(initial_progress)
        self.progress_bar.set_hexpand(True)
        
        # Initialize with progress bar as action widget
        super().__init__(icon, title, subtitle, self.progress_bar)
    
    def set_progress(self, fraction: float):
        """Set progress (0.0 to 1.0)."""
        self.progress_bar.set_fraction(max(0.0, min(1.0, fraction)))
    
    def set_text(self, text: str):
        """Set progress bar text."""
        self.progress_bar.set_text(text)
        self.progress_bar.set_show_text(True)


class ListWidget(Gtk.Box):
    """A scrollable list of clickable items with icons and text."""
    
    def __init__(self, height: int = 200, spacing: int = 4):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Create scrolled window
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scrolled_window.set_size_request(-1, height)
        self.scrolled_window.add_css_class("list-container")
        
        # Create list box for items
        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.list_box.add_css_class("list-widget")
        
        # Connect row activation signal
        self.list_box.connect("row-activated", self._on_row_activated)
        
        # Add list to scrolled window
        self.scrolled_window.set_child(self.list_box)
        self.append(self.scrolled_window)
        
        # Store callbacks for each item
        self._item_callbacks = {}
        
    def add_item(self, icon: str, title: str, subtitle: str = "", 
                 callback: Optional[Callable] = None, right_click_callback: Optional[Callable] = None, data=None) -> Gtk.ListBoxRow:
        """Add an item to the list."""
        
        # Create the row container
        row = Gtk.ListBoxRow()
        row.add_css_class("list-item")
        
        # Create main content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        content_box.set_margin_top(8)
        content_box.set_margin_bottom(8)
        content_box.set_margin_start(12)
        content_box.set_margin_end(12)
        
        # Icon
        icon_label = Gtk.Label(label=icon)
        icon_label.add_css_class("icon-label")
        icon_label.set_valign(Gtk.Align.CENTER)
        content_box.append(icon_label)
        
        # Text container
        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        text_box.set_hexpand(True)
        text_box.set_valign(Gtk.Align.CENTER)
        
        # Title
        title_label = Gtk.Label(label=title, xalign=0)
        title_label.add_css_class("title-label")
        text_box.append(title_label)
        
        # Subtitle (if provided)
        if subtitle:
            subtitle_label = Gtk.Label(label=subtitle, xalign=0)
            subtitle_label.add_css_class("subtitle-label")
            text_box.append(subtitle_label)
        
        content_box.append(text_box)
        
        # Store callbacks and data
        if callback or right_click_callback:
            self._item_callbacks[row] = {
                'left_click': (callback, data),
                'right_click': (right_click_callback, data)
            }
        
        # Add right-click gesture if callback provided
        if right_click_callback:
            gesture = Gtk.GestureClick()
            gesture.set_button(3)  # Right mouse button
            gesture.connect("pressed", lambda g, n, x, y: right_click_callback(row, data))
            row.add_controller(gesture)
        
        row.set_child(content_box)
        self.list_box.append(row)
        return row
    
    def clear_items(self):
        """Remove all items from the list."""
        # Clear callbacks
        self._item_callbacks.clear()
        
        # Remove all rows
        while True:
            row = self.list_box.get_first_child()
            if row is None:
                break
            self.list_box.remove(row)
    
    def _on_row_activated(self, list_box, row):
        """Handle row click/activation."""
        if row in self._item_callbacks:
            callback_info = self._item_callbacks[row]
            if isinstance(callback_info, dict):
                # New format with left/right click support
                callback, data = callback_info['left_click']
                if callback:
                    callback(row, data)
            else:
                # Old format for backward compatibility
                callback, data = callback_info
                if callback:
                    callback(row, data)
    
    def set_loading(self, loading: bool = True):
        """Show/hide loading state."""
        if loading:
            self.clear_items()
            self.add_item("", "Loading...", "Please wait")
        # Note: When not loading, the caller should call clear_items() and add real items
    
    def add_separator(self):
        """Add a visual separator to the list."""
        separator_row = Gtk.ListBoxRow()
        separator_row.set_selectable(False)
        separator_row.set_activatable(False)
        
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator.set_margin_top(4)
        separator.set_margin_bottom(4)
        separator_row.set_child(separator)
        
        self.list_box.append(separator_row)


class TabWidget(Gtk.Box):
    """A tabbed interface widget for multiple pages."""
    
    def __init__(self, tab_position: Gtk.PositionType = Gtk.PositionType.TOP):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Create notebook widget
        self.notebook = Gtk.Notebook()
        self.notebook.set_tab_pos(tab_position)
        self.notebook.add_css_class("tab-widget")
        
        self.append(self.notebook)
        
        # Store page data
        self._pages = {}
    
    def add_page(self, title: str, content: Gtk.Widget, icon: str = "") -> int:
        """Add a page to the tab widget."""
        
        # Create tab label
        if icon:
            tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            icon_label = Gtk.Label(label=icon)
            icon_label.add_css_class("icon-label")
            title_label = Gtk.Label(label=title)
            tab_box.append(icon_label)
            tab_box.append(title_label)
            tab_label = tab_box
        else:
            tab_label = Gtk.Label(label=title)
        
        # Add page to notebook
        page_num = self.notebook.append_page(content, tab_label)
        self._pages[page_num] = (title, content)
        
        return page_num
    
    def set_current_page(self, page_num: int):
        """Switch to the specified page."""
        self.notebook.set_current_page(page_num)
    
    def get_current_page(self) -> int:
        """Get the current page number."""
        return self.notebook.get_current_page()


class LoadingWidget(Gtk.Box):
    """A loading indicator widget with spinner and optional text."""
    
    def __init__(self, text: str = "Loading...", show_spinner: bool = True):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)
        self.add_css_class("loading-widget")
        
        if show_spinner:
            # Create spinner
            self.spinner = Gtk.Spinner()
            self.spinner.set_size_request(32, 32)
            self.spinner.start()
            self.append(self.spinner)
        
        # Create text label
        self.label = Gtk.Label(label=text)
        self.label.add_css_class("subtitle-label")
        self.append(self.label)
    
    def set_text(self, text: str):
        """Update the loading text."""
        self.label.set_text(text)
    
    def set_spinning(self, spinning: bool):
        """Start or stop the spinner."""
        if hasattr(self, 'spinner'):
            if spinning:
                self.spinner.start()
            else:
                self.spinner.stop()
