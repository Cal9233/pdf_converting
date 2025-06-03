"""
Progress window display for PDF to Excel Converter

This module provides a progress window to show conversion status and progress.
"""

import tkinter as tk
from tkinter import ttk
import time

from config import (
    PROGRESS_WINDOW_WIDTH,      # 350
    PROGRESS_WINDOW_HEIGHT,     # 150
    PROGRESS_BAR_SPEED,         # 10
    PROGRESS_UPDATE_INTERVAL    # 0.3
)


class ProgressWindow:
    """Handles the progress window display during PDF processing"""
    
    def __init__(self):
        self.progress_window = None
        self.status_label = None
        self.progress_bar = None
        self.file_label = None
        self._last_update = 0

    def show_progress_window(self):
        """Show a clean progress window to indicate the program is running"""
        try:
            self.progress_window = tk.Tk()
            self.progress_window.title("PDF to Excel Converter")
            self.progress_window.geometry(f"{PROGRESS_WINDOW_WIDTH}x{PROGRESS_WINDOW_HEIGHT}")
            self.progress_window.resizable(False, False)
            
            # Center the window
            self.progress_window.eval('tk::PlaceWindow . center')
            
            # Main frame
            main_frame = tk.Frame(self.progress_window, padx=20, pady=20)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Title
            title_label = tk.Label(main_frame, text="🏦 PDF to Excel Converter", 
                                 font=("Arial", 14, "bold"))
            title_label.pack(pady=(0, 15))
            
            # Status label
            self.status_label = tk.Label(main_frame, text="🚀 Starting conversion process...", 
                                       font=("Arial", 10))
            self.status_label.pack(pady=(0, 15))
            
            # Progress bar
            self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
            self.progress_bar.pack(fill=tk.X, pady=(0, 15))
            self.progress_bar.start(PROGRESS_BAR_SPEED)
            
            # Current file label
            self.file_label = tk.Label(main_frame, text="", 
                                     font=("Arial", 9), fg="gray")
            self.file_label.pack()
            
            # Don't allow closing
            self.progress_window.protocol("WM_DELETE_WINDOW", lambda: None)
            
            return self.progress_window
            
        except Exception:
            return None
    
    def update_progress(self, status_text, file_text="", force_update=False):
        """Update the progress window with current status"""
        try:
            if self.progress_window and (force_update or time.time() - getattr(self, '_last_update', 0) > PROGRESS_UPDATE_INTERVAL):
                self.status_label.config(text=status_text)
                if file_text:
                    self.file_label.config(text=file_text)
                self.progress_window.update_idletasks()
                self._last_update = time.time()
        except Exception:
            # Fallback to console only for critical updates
            if force_update:
                print(status_text)
    
    def close_progress_window(self):
        """Close the progress window"""
        try:
            if self.progress_window:
                self.progress_bar.stop()
                self.progress_window.destroy()
                self.progress_window = None
        except Exception:
            pass