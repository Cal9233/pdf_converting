# build.py - Save this in your project root (pdf_converter/)
"""
Complete final build script for PDF to Excel Converter
This version includes all dependency fixes and works with your project structure
"""

import os
import subprocess
import shutil
import sys

def check_dependencies():
    """Check that all required packages are installed"""
    required_packages = ['pdfplumber', 'pandas', 'openpyxl', 'tkinter']
    missing = []
    
    for package in required_packages:
        try:
            if package == 'tkinter':
                import tkinter
            else:
                __import__(package)
            print(f"✅ {package} installed")
        except ImportError:
            missing.append(package)
            print(f"❌ {package} missing")
    
    if missing:
        print(f"\n❌ Missing packages: {missing}")
        print("Install them with:")
        for pkg in missing:
            if pkg != 'tkinter':  # tkinter comes with Python
                print(f"  pip install {pkg}")
        return False
    
    print("✅ All dependencies found")
    return True

def main():
    print("🏗️  Building PDF to Excel Converter...")
    
    # Check dependencies first
    print("\n📦 Checking dependencies...")
    if not check_dependencies():
        return False
    
    # Clean previous builds
    for folder in ['build', 'dist', 'dist_final']:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"🧹 Cleaned {folder}")
    
    # Detect OS for correct path separator
    if sys.platform.startswith('win'):
        data_sep = ';'
    else:
        data_sep = ':'
    
    # Enhanced PyInstaller command with better dependency handling
    cmd = [
        'pyinstaller',
        '--onefile',                    # Single executable
        '--console',                    # Show console for debugging
        '--name', 'PDF_to_Excel_Converter',
        '--add-data', f'src{data_sep}src',        # Include src folder
        '--add-data', f'config{data_sep}config',  # Include config folder
        
        # Core dependencies
        '--hidden-import', 'pdfplumber',
        '--hidden-import', 'pdfplumber.page',
        '--hidden-import', 'pdfplumber.pdf',
        '--hidden-import', 'pdfplumber.utils',
        '--hidden-import', 'pandas',
        '--hidden-import', 'pandas.io.excel',
        '--hidden-import', 'openpyxl',
        '--hidden-import', 'openpyxl.workbook',
        '--hidden-import', 'openpyxl.worksheet',
        '--hidden-import', 'openpyxl.styles',
        
        # GUI dependencies
        '--hidden-import', 'tkinter',
        '--hidden-import', 'tkinter.ttk',
        '--hidden-import', 'tkinter.messagebox',
        
        # Your modules
        '--hidden-import', 'config',
        '--hidden-import', 'config.settings',
        '--hidden-import', 'src',
        '--hidden-import', 'src.core',
        '--hidden-import', 'src.core.converter',
        '--hidden-import', 'src.core.folder_manager',
        '--hidden-import', 'src.parsers',
        '--hidden-import', 'src.parsers.amex_parser',
        '--hidden-import', 'src.parsers.chase_parser',
        '--hidden-import', 'src.parsers.base_parser',
        '--hidden-import', 'src.validators',
        '--hidden-import', 'src.validators.transaction_validator',
        '--hidden-import', 'src.validators.name_validator',
        '--hidden-import', 'src.exporters',
        '--hidden-import', 'src.exporters.excel_exporter',
        '--hidden-import', 'src.ui',
        '--hidden-import', 'src.ui.progress_window',
        '--hidden-import', 'src.ui.completion_dialog',
        '--hidden-import', 'src.utils',
        '--hidden-import', 'src.utils.date_utils',
        '--hidden-import', 'src.utils.file_utils',
        '--hidden-import', 'src.utils.text_utils',
        
        # Additional Python modules that might be needed
        '--hidden-import', 'datetime',
        '--hidden-import', 'pathlib',
        '--hidden-import', 're',
        '--hidden-import', 'os',
        '--hidden-import', 'sys',
        '--hidden-import', 'time',
        
        # Collect all data from these packages
        '--collect-all', 'pdfplumber',
        '--collect-all', 'pandas',
        '--collect-all', 'openpyxl',
        
        'run.py'                        # Main entry point
    ]
    
    try:
        print("🔨 Running PyInstaller...")
        print(f"Command: pyinstaller --onefile --console --name PDF_to_Excel_Converter ...")
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Build successful!")
        
        # Create distribution folder
        os.makedirs('dist_final', exist_ok=True)
        
        # Copy executable (adjust for macOS)
        if sys.platform.startswith('win'):
            exe_name = 'PDF_to_Excel_Converter.exe'
        else:
            exe_name = 'PDF_to_Excel_Converter'
            
        exe_source = os.path.join('dist', exe_name)
        if os.path.exists(exe_source):
            shutil.copy2(exe_source, f'dist_final/{exe_name}')
            print(f"✅ Copied executable to dist_final/{exe_name}")
        else:
            print(f"❌ Executable not found at {exe_source}!")
            return False
        
        # Create required folders
        for folder in ['Convert', 'Excel', 'logs']:
            folder_path = os.path.join('dist_final', folder)
            os.makedirs(folder_path, exist_ok=True)
            print(f"✅ Created {folder}/ folder")
        
        # Copy documentation
        if os.path.exists('README.md'):
            shutil.copy2('README.md', 'dist_final/README.md')
            print("✅ Copied README.md")
        
        # Create instructions
        instructions = """PDF to Excel Converter - Instructions

1. Put your PDF bank statements in the 'Convert' folder
2. Double-click 'PDF_to_Excel_Converter' (or PDF_to_Excel_Converter.exe on Windows)
3. Wait for processing to complete
4. Find Excel files in the 'Excel' folder

Supports: American Express and Chase statements

Troubleshooting:
- Make sure PDFs are credit card statements (not other documents)
- Check console output for any error messages
- Ensure you have permission to write to the Excel folder
"""
        with open('dist_final/INSTRUCTIONS.txt', 'w') as f:
            f.write(instructions)
        
        print(f"\n🎉 Build complete!")
        print(f"📦 Everything ready in 'dist_final' folder")
        print(f"\n📋 Test it:")
        print(f"1. Add a test PDF to dist_final/Convert/")
        if sys.platform.startswith('win'):
            print(f"2. Run dist_final/PDF_to_Excel_Converter.exe")
        else:
            print(f"2. Run ./dist_final/PDF_to_Excel_Converter")
        print(f"3. Check for Excel files in dist_final/Excel/")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print("❌ Build failed!")
        if e.stderr:
            print("Error:", e.stderr)
        if e.stdout:
            print("Output:", e.stdout)
        return False
        
    except FileNotFoundError:
        print("❌ PyInstaller not found!")
        print("Install it with: pip install pyinstaller")
        return False

if __name__ == "__main__":
    if not main():
        input("Press Enter to exit...")
        sys.exit(1)