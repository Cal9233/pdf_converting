#!/usr/bin/env python3
"""
Debug version of PDF to Excel Converter
Shows detailed output about what's happening
"""

import os
import sys
import time

def main():
    print("="*60)
    print("PDF to Excel Converter - Debug Version")
    print("="*60)
    
    # Show current location
    if getattr(sys, 'frozen', False):
        # Running as exe
        base_dir = os.path.dirname(sys.executable)
        print(f"Running as EXE from: {base_dir}")
    else:
        # Running as script
        base_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"Running as script from: {base_dir}")
    
    print(f"Working directory: {os.getcwd()}")
    
    # Check folder structure
    print("\nChecking folder structure...")
    
    convert_dir = os.path.join(base_dir, 'Convert')
    excel_dir = os.path.join(base_dir, 'Excel')
    
    if not os.path.exists(convert_dir):
        print(f"❌ ERROR: Convert folder not found at {convert_dir}")
        print("Please create a 'Convert' folder in the same directory as this program")
    else:
        print(f"✅ Convert folder found")
        
        # Check subdirectories
        for subdir in ['amex', 'chase', 'w2', 'other']:
            subdir_path = os.path.join(convert_dir, subdir)
            if os.path.exists(subdir_path):
                # Count PDFs
                try:
                    files = os.listdir(subdir_path)
                    pdfs = [f for f in files if f.lower().endswith('.pdf')]
                    print(f"  ✅ {subdir:6} - {len(pdfs)} PDF files")
                    if pdfs and len(pdfs) <= 3:
                        for pdf in pdfs:
                            print(f"            - {pdf}")
                except Exception as e:
                    print(f"  ❌ {subdir:6} - Error reading: {e}")
            else:
                print(f"  ❌ {subdir:6} - Folder missing")
    
    if not os.path.exists(excel_dir):
        print(f"\n❌ Excel folder not found - will create it")
        try:
            os.makedirs(excel_dir)
            print(f"✅ Created Excel folder")
        except Exception as e:
            print(f"❌ Failed to create Excel folder: {e}")
    else:
        print(f"\n✅ Excel folder found")
    
    # Try to import required modules
    print("\nChecking Python modules...")
    modules = ['pandas', 'pdfplumber', 'openpyxl']
    missing = []
    
    for module in modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError:
            print(f"  ❌ {module} - NOT INSTALLED")
            missing.append(module)
    
    if missing:
        print(f"\n❌ Missing modules: {', '.join(missing)}")
        print("Install with: pip install " + ' '.join(missing))
    
    # Show next steps
    print("\n" + "="*60)
    if os.path.exists(convert_dir) and not missing:
        print("✅ Setup looks good!")
        print("\nNext steps:")
        print("1. Place PDF files in the Convert subfolders")
        print("2. Run the main converter program")
        print("3. Check the Excel folder for output")
    else:
        print("❌ Setup needs attention - see errors above")
    
    print("\nPress Enter to exit...")
    input()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("\nPress Enter to exit...")
        input()