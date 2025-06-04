#!/usr/bin/env python3
"""
Test script to verify exe path detection
This helps debug folder path issues
"""

import os
import sys
import tkinter as tk
from tkinter import scrolledtext

def test_paths():
    """Test and display path information"""
    info = []
    
    # Check if running as exe
    is_frozen = getattr(sys, 'frozen', False)
    info.append(f"Running as EXE: {is_frozen}")
    info.append(f"sys.executable: {sys.executable}")
    
    # Determine base directory
    if is_frozen:
        base_dir = os.path.dirname(sys.executable)
        info.append(f"EXE directory: {base_dir}")
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        info.append(f"Script directory: {base_dir}")
    
    info.append(f"\nBase directory: {base_dir}")
    
    # Check expected folders
    convert_dir = os.path.join(base_dir, 'Convert')
    excel_dir = os.path.join(base_dir, 'Excel')
    
    info.append(f"\nExpected folders:")
    info.append(f"Convert: {convert_dir}")
    info.append(f"  Exists: {os.path.exists(convert_dir)}")
    info.append(f"Excel: {excel_dir}")
    info.append(f"  Exists: {os.path.exists(excel_dir)}")
    
    # Check subdirectories
    subdirs = ['amex', 'chase', 'other', 'w2']
    info.append(f"\nSubdirectories:")
    for subdir in subdirs:
        subdir_path = os.path.join(convert_dir, subdir)
        exists = os.path.exists(subdir_path)
        info.append(f"  {subdir}: {exists}")
        
        # Count PDFs if exists
        if exists:
            pdf_count = len([f for f in os.listdir(subdir_path) if f.lower().endswith('.pdf')])
            info.append(f"    PDF files: {pdf_count}")
    
    # List all files in base directory
    info.append(f"\nFiles in base directory:")
    try:
        files = os.listdir(base_dir)
        for f in sorted(files)[:10]:  # Show first 10
            info.append(f"  - {f}")
        if len(files) > 10:
            info.append(f"  ... and {len(files) - 10} more files")
    except Exception as e:
        info.append(f"  Error listing files: {e}")
    
    # Current working directory
    info.append(f"\nCurrent working directory: {os.getcwd()}")
    
    return "\n".join(info)

class PathTestGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("EXE Path Test")
        self.root.geometry("600x500")
        
        # Create text widget
        self.text = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, width=70, height=30)
        self.text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Run test button
        test_btn = tk.Button(self.root, text="Run Path Test", command=self.run_test)
        test_btn.pack(pady=5)
        
        # Close button
        close_btn = tk.Button(self.root, text="Close", command=self.root.quit)
        close_btn.pack(pady=5)
        
        # Run test automatically
        self.run_test()
    
    def run_test(self):
        """Run the path test and display results"""
        self.text.delete(1.0, tk.END)
        self.text.insert(tk.END, "🔍 Path Detection Test\n")
        self.text.insert(tk.END, "=" * 50 + "\n\n")
        
        result = test_paths()
        self.text.insert(tk.END, result)
        
        # Add recommendations
        self.text.insert(tk.END, "\n\n📋 Recommendations:\n")
        self.text.insert(tk.END, "=" * 50 + "\n")
        
        if getattr(sys, 'frozen', False):
            self.text.insert(tk.END, "✅ Running as compiled EXE\n")
            base_dir = os.path.dirname(sys.executable)
            if not os.path.exists(os.path.join(base_dir, 'Convert')):
                self.text.insert(tk.END, "❌ Convert folder not found!\n")
                self.text.insert(tk.END, "   Create these folders next to your EXE:\n")
                self.text.insert(tk.END, "   - Convert/\n")
                self.text.insert(tk.END, "     - amex/\n")
                self.text.insert(tk.END, "     - chase/\n")
                self.text.insert(tk.END, "     - other/\n")
                self.text.insert(tk.END, "     - w2/\n")
                self.text.insert(tk.END, "   - Excel/\n")
            else:
                self.text.insert(tk.END, "✅ Folder structure looks good!\n")
        else:
            self.text.insert(tk.END, "📝 Running as Python script\n")
            self.text.insert(tk.END, "   To create EXE, run:\n")
            self.text.insert(tk.END, "   pyinstaller --onefile --windowed test_exe_paths.py\n")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    # If running without GUI (for testing)
    if len(sys.argv) > 1 and sys.argv[1] == "--no-gui":
        print(test_paths())
    else:
        app = PathTestGUI()
        app.run()