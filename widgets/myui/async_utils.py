"""
Async utilities for MyUI - Thread-safe command execution and progress monitoring
===============================================================================

This module provides threading utilities that integrate safely with GTK's main loop,
enabling non-blocking operations like bluetooth scanning, network discovery, etc.

Key Components:
- ThreadRunner: Execute commands in background threads with progress callbacks
- AsyncCommand: Wrapper for subprocess execution with real-time output streaming
- ProgressMonitor: Track operation progress with cancellation support
"""

import threading
import subprocess
import time
import queue
from typing import Optional, Callable, Dict, Any, List
from gi.repository import GLib, Gtk


class AsyncCommand:
    """Execute subprocess commands asynchronously with real-time output streaming."""
    
    def __init__(self, command: List[str], timeout: Optional[float] = None):
        self.command = command
        self.timeout = timeout
        self.process = None
        self.cancelled = False
        self.output_lines = []
        self.error_lines = []
        
    def cancel(self):
        """Cancel the running command."""
        self.cancelled = True
        if self.process:
            self.process.terminate()
            
    def run(self, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Run the command and return results."""
        if self.cancelled:
            return {"success": False, "error": "Command was cancelled"}
            
        try:
            self.process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Read output line by line for progress updates
            while True:
                if self.cancelled:
                    self.process.terminate()
                    return {"success": False, "error": "Command was cancelled"}
                    
                output = self.process.stdout.readline()
                if output == '' and self.process.poll() is not None:
                    break
                    
                if output:
                    line = output.strip()
                    self.output_lines.append(line)
                    if progress_callback:
                        # Use GLib.idle_add to safely call GTK from thread
                        GLib.idle_add(progress_callback, "output", line)
                        
            # Get any remaining output
            stdout, stderr = self.process.communicate(timeout=self.timeout)
            if stdout:
                self.output_lines.extend(stdout.strip().split('\n'))
            if stderr:
                self.error_lines.extend(stderr.strip().split('\n'))
                
            return_code = self.process.returncode
            
            return {
                "success": return_code == 0,
                "return_code": return_code,
                "output": self.output_lines,
                "error": self.error_lines,
                "command": ' '.join(self.command)
            }
            
        except subprocess.TimeoutExpired:
            if self.process:
                self.process.kill()
            return {"success": False, "error": f"Command timed out after {self.timeout}s"}
        except Exception as e:
            return {"success": False, "error": f"Command failed: {str(e)}"}


class ProgressMonitor:
    """Monitor progress of long-running operations with cancellation support."""
    
    def __init__(self, operation_name: str = "Operation"):
        self.operation_name = operation_name
        self.cancelled = False
        self.progress = 0.0
        self.status = "Starting..."
        self.callbacks = []
        
    def add_callback(self, callback: Callable):
        """Add a callback to receive progress updates."""
        self.callbacks.append(callback)
        
    def update_progress(self, progress: float, status: str = None):
        """Update progress (0.0 to 1.0) and optional status text."""
        if self.cancelled:
            return
            
        self.progress = max(0.0, min(1.0, progress))
        if status:
            self.status = status
            
        # Notify all callbacks via GTK main loop
        for callback in self.callbacks:
            GLib.idle_add(callback, self.progress, self.status)
            
    def cancel(self):
        """Cancel the operation."""
        self.cancelled = True
        self.status = "Cancelled"
        for callback in self.callbacks:
            GLib.idle_add(callback, self.progress, self.status)


class ThreadRunner:
    """Execute functions in background threads with GTK-safe result callbacks."""
    
    def __init__(self):
        self.active_threads = {}
        self.thread_counter = 0
        
    def run_async(self, 
                  target_func: Callable, 
                  args: tuple = (), 
                  kwargs: dict = None,
                  success_callback: Optional[Callable] = None,
                  error_callback: Optional[Callable] = None,
                  progress_callback: Optional[Callable] = None,
                  thread_name: Optional[str] = None) -> str:
        """
        Run a function in a background thread with GTK-safe callbacks.
        
        Args:
            target_func: Function to run in background thread
            args: Arguments to pass to target_func
            kwargs: Keyword arguments to pass to target_func
            success_callback: Called with result when function succeeds
            error_callback: Called with exception when function fails
            progress_callback: Called with progress updates (if target_func supports it)
            thread_name: Optional name for the thread
            
        Returns:
            thread_id: Unique identifier for this thread
        """
        if kwargs is None:
            kwargs = {}
            
        self.thread_counter += 1
        thread_id = f"thread_{self.thread_counter}"
        
        if thread_name:
            thread_id = f"{thread_name}_{self.thread_counter}"
            
        def thread_worker():
            """Worker function that runs in the background thread."""
            try:
                # Add progress callback to kwargs if target function supports it
                if progress_callback and 'progress_callback' in target_func.__code__.co_varnames:
                    kwargs['progress_callback'] = progress_callback
                    
                result = target_func(*args, **kwargs)
                
                # Use GLib.idle_add to safely call GTK callbacks from thread
                if success_callback:
                    GLib.idle_add(self._safe_callback, success_callback, result, thread_id)
                    
            except Exception as e:
                if error_callback:
                    GLib.idle_add(self._safe_callback, error_callback, e, thread_id)
            finally:
                # Remove from active threads
                if thread_id in self.active_threads:
                    del self.active_threads[thread_id]
                    
        # Create and start thread
        thread = threading.Thread(target=thread_worker, name=thread_id)
        thread.daemon = True
        self.active_threads[thread_id] = thread
        thread.start()
        
        return thread_id
        
    def _safe_callback(self, callback: Callable, data: Any, thread_id: str) -> bool:
        """Safely execute callback in GTK main loop."""
        try:
            callback(data)
        except Exception as e:
            print(f"Error in thread callback {thread_id}: {e}")
        return False  # Don't repeat the callback
        
    def cancel_thread(self, thread_id: str):
        """Cancel a running thread (if possible)."""
        if thread_id in self.active_threads:
            thread = self.active_threads[thread_id]
            # Note: Python threads can't be forcefully killed
            # The target function must check for cancellation itself
            print(f"Cancellation requested for thread {thread_id}")
            
    def get_active_threads(self) -> List[str]:
        """Get list of currently active thread IDs."""
        return list(self.active_threads.keys())
        
    def wait_for_all(self, timeout: Optional[float] = None):
        """Wait for all active threads to complete."""
        for thread_id, thread in self.active_threads.items():
            thread.join(timeout=timeout)


# Global thread runner instance
_thread_runner = ThreadRunner()

def run_async(target_func: Callable, 
              args: tuple = (), 
              kwargs: dict = None,
              success_callback: Optional[Callable] = None,
              error_callback: Optional[Callable] = None,
              progress_callback: Optional[Callable] = None,
              thread_name: Optional[str] = None) -> str:
    """
    Convenience function to run a function asynchronously.
    
    This is a wrapper around ThreadRunner.run_async() using a global instance.
    """
    return _thread_runner.run_async(
        target_func, args, kwargs, 
        success_callback, error_callback, progress_callback, thread_name
    )

def cancel_async(thread_id: str):
    """Cancel a running async operation."""
    _thread_runner.cancel_thread(thread_id)

def get_active_async() -> List[str]:
    """Get list of currently active async operations."""
    return _thread_runner.get_active_threads()