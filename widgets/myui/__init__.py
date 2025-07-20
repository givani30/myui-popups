"""
MyUI - A personal UI toolkit for Waybar popups
==============================================

This package provides reusable components for creating consistent,
themed popup windows that integrate with your Waybar setup.

Modules:
- theming: CSS loading and application
- widgets: Reusable UI components
- base_window: Standard popup window behavior
"""

__version__ = "0.1.0"
__author__ = "Your Name"

# Make key classes easily importable
from .base_window import AppWindow, QuickApp
from .components.widgets import SliderRow, ButtonRow, InfoRow, ToggleRow, ProgressRow, ListWidget, TabWidget, LoadingWidget
from .theming import apply_theme
from .async_utils import ThreadRunner, AsyncCommand, ProgressMonitor, run_async, cancel_async, get_active_async

__all__ = ['AppWindow', 'QuickApp', 'SliderRow', 'ButtonRow', 'InfoRow', 'ToggleRow', 'ProgressRow', 'ListWidget', 'TabWidget', 'LoadingWidget', 'apply_theme', 'ThreadRunner', 'AsyncCommand', 'ProgressMonitor', 'run_async', 'cancel_async', 'get_active_async']
