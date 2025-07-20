"""
Base Window module for MyUI
===========================

Provides a standard popup window that all scripts can inherit from.
Handles theming, focus behavior, and common window configuration.
"""

import sys
from typing import Optional

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib

from . import theming


class AppWindow(Adw.ApplicationWindow):
    """A base window for all our popups with automatic theming and behavior."""
    
    def __init__(self, app, title: str = "MyUI Popup", width: int = 350, height: int = -1,
                 close_on_focus_loss: bool = True, window_tag: str = "popup"):
        super().__init__(application=app)
        
        # Apply the centralized theme
        theming.apply_theme()

        # Standard popup configuration
        self.set_decorated(False)
        self.set_default_size(width, height)  # -1 means auto-size height
        self.set_title(title)
        
        # Set window tag for Hyprland window management
        self._set_window_tag(window_tag)
        
        # Set window tag for Hyprland window management
        self._set_window_tag(window_tag)
        
        # --- Stability Improvement: Focus Loss Grace Period ---
        self._close_timeout_id = None
        self._can_close_on_focus_loss = False # Disabled by default
        
        # Optional: Close window when it loses focus (with timeout to prevent instant close)
        if close_on_focus_loss:
            event_controller = Gtk.EventControllerFocus()
            event_controller.connect("leave", self.on_focus_leave)
            event_controller.connect("enter", self.on_focus_enter)
            self.add_controller(event_controller)
            # Enable closing after a 200ms grace period
            GLib.timeout_add(200, self.enable_focus_loss_close)
        
        # Set up default content container with padding
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.main_box.set_margin_top(20)
        self.main_box.set_margin_bottom(20)
        self.main_box.set_margin_start(20)
        self.main_box.set_margin_end(20)
        self.set_content(self.main_box)

    def enable_focus_loss_close(self):
        """Callback to enable the focus-loss-close behavior after a grace period."""
        self._can_close_on_focus_loss = True
        return GLib.SOURCE_REMOVE # Prevents the timer from running again

    def _set_window_tag(self, tag: str):
        """Set a window tag for Hyprland window management."""
        try:
            # The application ID is already set by the QuickApp when window_tag is provided
            # We can also set window properties that Hyprland can use
            print(f"DEBUG: Window tag '{tag}' set for Hyprland (app_id: myui.{tag})", file=sys.stderr)
        except Exception as e:
            print(f"DEBUG: Could not set window tag: {e}", file=sys.stderr)

    def on_focus_leave(self, controller):
        """Start timeout to close window when it loses focus."""
        if not self._can_close_on_focus_loss:
            return
            
        # Cancel any existing timeout
        if hasattr(self, '_close_timeout_id') and self._close_timeout_id:
            GLib.source_remove(self._close_timeout_id)
        
        # Set timeout to close after 500ms of no focus
        self._close_timeout_id = GLib.timeout_add(500, self._close_timeout)
    
    def on_focus_enter(self, controller):
        """Cancel close timeout when focus returns."""
        # Cancel the close timeout if focus returns
        if hasattr(self, '_close_timeout_id') and self._close_timeout_id:
            GLib.source_remove(self._close_timeout_id)
            self._close_timeout_id = None
    
    def _close_timeout(self):
        """Close the window after timeout."""
        self.close()
        self._close_timeout_id = None
        return GLib.SOURCE_REMOVE
    
    def add_widget(self, widget: Gtk.Widget):
        """Add a widget to the main container."""
        self.main_box.append(widget)
    
    def add_separator(self):
        """Add a visual separator to the layout."""
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator.set_margin_top(5)
        separator.set_margin_bottom(5)
        self.main_box.append(separator)
    
    def add_title(self, title: str, subtitle: str = ""):
        """Add a title section to the popup."""
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        
        title_label = Gtk.Label(label=title, xalign=0)
        title_label.add_css_class("title-label")
        title_box.append(title_label)
        
        if subtitle:
            subtitle_label = Gtk.Label(label=subtitle, xalign=0)
            subtitle_label.add_css_class("subtitle-label")
            title_box.append(subtitle_label)
        
        self.main_box.append(title_box)


class QuickApp(Adw.Application):
    """A quick application class for simple popup scripts."""
    
    def __init__(self, application_id: str, window_class=AppWindow, window_tag: Optional[str] = None, **window_kwargs):
        # If window_tag is provided, use it to create a unique application_id
        if window_tag:
            application_id = f"myui.{window_tag}"
            
        super().__init__(application_id=application_id)
        self.window_class = window_class
        self.window_kwargs = window_kwargs
        
        # Pass window_tag to the window if not already specified
        if window_tag and 'window_tag' not in window_kwargs:
            self.window_kwargs['window_tag'] = window_tag
            
        self.connect('activate', self.on_activate)
    
    def on_activate(self, app):
        """Create and show the window."""
        self.win = self.window_class(app=app, **self.window_kwargs)
        self.win.present()
    
    def run_quick(self):
        """Convenience method to run the app quickly."""
        import sys
        self.run(sys.argv)
