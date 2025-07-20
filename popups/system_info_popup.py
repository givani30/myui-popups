#!/usr/bin/env python3
"""
System Info Popup using MyUI
============================

A quick system information popup demonstrating InfoRow and ProgressRow widgets.
This shows how easy it is to create new popups with MyUI.
"""

import sys
import subprocess
import shutil
from pathlib import Path

# Add current directory to path so we can import myui
sys.path.insert(0, str(Path(__file__).parent))

from widgets.myui import AppWindow, InfoRow, ProgressRow, ButtonRow
from widgets.myui.base_window import QuickApp


class SystemInfoPopup(AppWindow):
    """System information popup with live data."""
    
    def __init__(self, app, **kwargs):
        # Extract window_tag and pass other kwargs to parent
        window_tag = kwargs.pop('window_tag', 'systeminfo')
        super().__init__(
            app=app, 
            title="System Information",
            width=380,
            close_on_focus_loss=False,  # Keep open for viewing
            window_tag=window_tag,
            **kwargs
        )
        
        # Add title
        self.add_title("System Overview", "Current system status and resources")
        
        # Get system info
        self.update_system_info()
        
        self.add_separator()
        
        # Action buttons
        button_row = ButtonRow(spacing=8)
        button_row.add_button("Refresh", self.on_refresh, icon="🔄")
        button_row.add_button("Close", self.on_close, icon="❌")
        self.add_widget(button_row)

    def update_system_info(self):
        """Update all system information displays."""
        # Clear existing widgets (except title and buttons)
        for child in list(self.main_box):
            if hasattr(child, 'get_css_classes'):
                if 'title-label' not in child.get_css_classes():
                    self.main_box.remove(child)
        
        # Recreate title and separator
        self.add_title("System Overview", "Current system status and resources")
        
        # CPU Info
        try:
            cpu_info = self.get_cpu_info()
            self.add_widget(InfoRow(
                icon="🖥️",
                title="CPU",
                subtitle=f"{cpu_info['model']} • {cpu_info['cores']} cores"
            ))
            
            # CPU usage progress
            cpu_usage = self.get_cpu_usage()
            cpu_progress = ProgressRow(
                icon="📊",
                title="CPU Usage",
                subtitle=f"{cpu_usage}% utilization",
                initial_progress=cpu_usage / 100
            )
            self.add_widget(cpu_progress)
            
        except Exception as e:
            self.add_widget(InfoRow(
                icon="⚠️",
                title="CPU",
                subtitle=f"Could not read CPU info: {e}"
            ))
        
        # Memory Info
        try:
            memory_info = self.get_memory_info()
            memory_progress = ProgressRow(
                icon="🧠",
                title="Memory",
                subtitle=f"{memory_info['used_gb']:.1f} GB / {memory_info['total_gb']:.1f} GB",
                initial_progress=memory_info['usage_percent'] / 100
            )
            memory_progress.set_text(f"{memory_info['usage_percent']:.0f}%")
            self.add_widget(memory_progress)
            
        except Exception as e:
            self.add_widget(InfoRow(
                icon="⚠️",
                title="Memory",
                subtitle=f"Could not read memory info: {e}"
            ))
        
        # Disk Usage
        try:
            disk_info = self.get_disk_info()
            disk_progress = ProgressRow(
                icon="💾",
                title="Disk Usage (/)",
                subtitle=f"{disk_info['used_gb']:.1f} GB / {disk_info['total_gb']:.1f} GB",
                initial_progress=disk_info['usage_percent'] / 100
            )
            disk_progress.set_text(f"{disk_info['usage_percent']:.0f}%")
            self.add_widget(disk_progress)
            
        except Exception as e:
            self.add_widget(InfoRow(
                icon="⚠️",
                title="Disk",
                subtitle=f"Could not read disk info: {e}"
            ))
        
        # Uptime
        try:
            uptime = self.get_uptime()
            self.add_widget(InfoRow(
                icon="⏱️",
                title="Uptime",
                subtitle=uptime
            ))
        except Exception:
            self.add_widget(InfoRow(
                icon="⏱️",
                title="Uptime",
                subtitle="Unknown"
            ))
    
    def get_cpu_info(self):
        """Get CPU information."""
        try:
            # Get CPU model
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line.startswith('model name'):
                        model = line.split(':')[1].strip()
                        break
                else:
                    model = "Unknown CPU"
            
            # Get CPU core count
            cores = subprocess.run(['nproc'], capture_output=True, text=True)
            core_count = cores.stdout.strip() if cores.returncode == 0 else "?"
            
            return {
                'model': model.replace('(R)', '').replace('(TM)', ''),
                'cores': core_count
            }
        except:
            return {'model': 'Unknown CPU', 'cores': '?'}
    
    def get_cpu_usage(self):
        """Get current CPU usage percentage."""
        try:
            # Quick and dirty CPU usage
            result = subprocess.run(
                ['top', '-bn1'], 
                capture_output=True, text=True, timeout=2
            )
            for line in result.stdout.split('\n'):
                if '%Cpu(s):' in line:
                    # Extract idle percentage and calculate usage
                    parts = line.split(',')
                    for part in parts:
                        if 'id' in part:  # idle
                            idle = float(part.split()[0])
                            return round(100 - idle, 1)
            return 0
        except:
            return 0
    
    def get_memory_info(self):
        """Get memory usage information."""
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            
            # Parse memory info
            total_kb = int([line for line in meminfo.split('\n') if 'MemTotal:' in line][0].split()[1])
            available_kb = int([line for line in meminfo.split('\n') if 'MemAvailable:' in line][0].split()[1])
            
            total_gb = total_kb / 1024 / 1024
            available_gb = available_kb / 1024 / 1024
            used_gb = total_gb - available_gb
            usage_percent = (used_gb / total_gb) * 100
            
            return {
                'total_gb': total_gb,
                'used_gb': used_gb,
                'usage_percent': usage_percent
            }
        except:
            return {'total_gb': 0, 'used_gb': 0, 'usage_percent': 0}
    
    def get_disk_info(self):
        """Get disk usage for root filesystem."""
        try:
            total, used, free = shutil.disk_usage('/')
            total_gb = total / 1024**3
            used_gb = used / 1024**3
            usage_percent = (used / total) * 100
            
            return {
                'total_gb': total_gb,
                'used_gb': used_gb,
                'usage_percent': usage_percent
            }
        except:
            return {'total_gb': 0, 'used_gb': 0, 'usage_percent': 0}
    
    def get_uptime(self):
        """Get system uptime."""
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.read().split()[0])
            
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            
            if days > 0:
                return f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        except:
            return "Unknown"
    
    def on_refresh(self, button):
        """Refresh system information."""
        print("🔄 Refreshing system info...")
        self.update_system_info()
        
        # Re-add separator and buttons
        self.add_separator()
        button_row = ButtonRow(spacing=8)
        button_row.add_button("Refresh", self.on_refresh, icon="🔄")
        button_row.add_button("Close", self.on_close, icon="❌")
        self.add_widget(button_row)
    
    def on_close(self, button):
        """Close the popup."""
        print("❌ Closing system info")
        self.close()


if __name__ == "__main__":
    app = QuickApp(
        application_id="com.example.SystemInfo",
        window_class=SystemInfoPopup,
        window_tag="systeminfo"
    )
    app.run_quick()
