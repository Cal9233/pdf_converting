#!/usr/bin/env python3
"""
Debug GUI version of PDF to Excel Converter
Shows detailed output in a window
"""

import os
import sys
import tkinter as tk
from tkinter import scrolledtext
import threading

class DebugWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PDF Converter - Debug Info")
        self.root.geometry("800x600")
        
        # Create text area with scrollbar
        self.text_area = scrolledtext.ScrolledText(
            self.root, 
            wrap=tk.WORD, 
            width=80, 
            height=30,
            font=("Courier", 10)
        )
        self.text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Create close button
        self.close_button = tk.Button(
            self.root, 
            text="Close", 
            command=self.root.quit,
            height=2,
            width=20
        )
        self.close_button.pack(pady=5)
        
        # Run debug checks
        self.run_debug()
        
    def write(self, text):
        """Write text to the window"""
        self.text_area.insert(tk.END, text + "\n")
        self.text_area.see(tk.END)
        self.root.update()
        
    def run_debug(self):
        """Run all debug checks"""
        self.write("="*60)
        self.write("PDF to Excel Converter - Debug Report")
        self.write("="*60)
        
        # Show current location
        if getattr(sys, 'frozen', False):
            # Running as exe
            base_dir = os.path.dirname(sys.executable)
            self.write(f"Running as EXE from: {base_dir}")
        else:
            # Running as script
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.write(f"Running as script from: {base_dir}")
        
        self.write(f"Working directory: {os.getcwd()}")
        
        # Check folder structure
        self.write("\nChecking folder structure...")
        
        convert_dir = os.path.join(base_dir, 'Convert')
        excel_dir = os.path.join(base_dir, 'Excel')
        
        if not os.path.exists(convert_dir):
            self.write(f"❌ ERROR: Convert folder not found at {convert_dir}")
            self.write("   ACTION: Create a 'Convert' folder next to the exe")
        else:
            self.write(f"✅ Convert folder found")
            
            # Check subdirectories
            total_pdfs = 0
            for subdir in ['amex', 'chase', 'w2', 'other']:
                subdir_path = os.path.join(convert_dir, subdir)
                if os.path.exists(subdir_path):
                    # Count PDFs
                    try:
                        files = os.listdir(subdir_path)
                        pdfs = [f for f in files if f.lower().endswith('.pdf')]
                        total_pdfs += len(pdfs)
                        self.write(f"  ✅ {subdir:6} - {len(pdfs)} PDF files")
                        if pdfs and len(pdfs) <= 3:
                            for pdf in pdfs:
                                self.write(f"            - {pdf}")
                    except Exception as e:
                        self.write(f"  ❌ {subdir:6} - Error reading: {e}")
                else:
                    self.write(f"  ❌ {subdir:6} - Folder missing")
                    self.write(f"     ACTION: Create folder at {subdir_path}")
            
            if total_pdfs == 0:
                self.write("\n⚠️  WARNING: No PDF files found in any folder!")
                self.write("   ACTION: Place PDF files in the appropriate Convert subfolders")
        
        if not os.path.exists(excel_dir):
            self.write(f"\n⚠️  Excel folder not found - will be created when needed")
        else:
            self.write(f"\n✅ Excel folder found")
            # Check for output files
            try:
                excel_files = [f for f in os.listdir(excel_dir) if f.endswith('.xlsx')]
                if excel_files:
                    self.write(f"   Found {len(excel_files)} Excel files:")
                    for f in excel_files:
                        self.write(f"   - {f}")
            except:
                pass
        
        # Try to import required modules
        self.write("\nChecking Python modules...")
        modules = ['pandas', 'pdfplumber', 'openpyxl']
        missing = []
        
        for module in modules:
            try:
                __import__(module)
                self.write(f"  ✅ {module} - installed")
            except ImportError:
                self.write(f"  ❌ {module} - NOT INSTALLED")
                missing.append(module)
        
        if missing:
            self.write(f"\n❌ ERROR: Missing required modules: {', '.join(missing)}")
            self.write("   This exe may not work properly!")
            self.write("   The exe should include these, so it may be corrupted.")
        
        # Check for the main converter script
        self.write("\nChecking for converter files...")
        converter_files = ['run_converter.py', 'pdf_to_excel_converter.py']
        found_any = False
        
        for file in converter_files:
            file_path = os.path.join(base_dir, file)
            if os.path.exists(file_path):
                self.write(f"  ✅ {file} found")
                found_any = True
            else:
                self.write(f"  ℹ️  {file} not found (OK if using exe)")
        
        # Summary
        self.write("\n" + "="*60)
        self.write("SUMMARY:")
        self.write("="*60)
        
        if os.path.exists(convert_dir) and not missing:
            self.write("✅ Basic setup looks good!")
            self.write("\nPOSSIBLE ISSUES:")
            self.write("1. The exe might be built from old code")
            self.write("2. No PDF files found to process")
            self.write("\nRECOMMENDATIONS:")
            self.write("1. Place PDF files in Convert/amex/ or Convert/chase/")
            self.write("2. Rebuild the exe with the latest run_converter.py")
            self.write("3. Try running from command prompt to see errors")
        else:
            self.write("❌ Setup needs attention - see errors above")
            
        self.write("\n" + "="*60)
        self.write("Click 'Close' to exit")
        
    def run(self):
        self.root.mainloop()

def main():
    app = DebugWindow()
    app.run()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Fallback for any errors
        import tkinter.messagebox as mb
        mb.showerror("Error", f"Debug tool failed:\n{str(e)}")