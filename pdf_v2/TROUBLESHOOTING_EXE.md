# Troubleshooting PDF to Excel Converter .exe

## Issue: Program runs but nothing happens

### Most Common Causes:

1. **Old .exe version** - The .exe might be built from old code without the recent updates
2. **Missing Python script** - Some builds need the .py file alongside the .exe
3. **No PDF files** - The program exits quickly if no PDFs are found
4. **Wrong folder structure** - The folders might not be set up correctly

## Solution Steps:

### Step 1: Check Your Folder Structure
Your custom folder should look like this:
```
YourFolder/
├── PDF_to_Excel_Converter.exe
├── Convert/
│   ├── amex/       (put AmEx PDFs here)
│   ├── chase/      (put Chase PDFs here)
│   ├── w2/         (put W2 PDFs here)
│   └── other/      (put other PDFs here)
└── Excel/          (output files will appear here)
```

### Step 2: Test with PDF Files
1. Put at least one PDF in Convert/amex/ or Convert/chase/
2. Run the .exe again
3. Check if files appear in the Excel folder

### Step 3: Run from Command Prompt (to see errors)
1. Open Command Prompt
2. Navigate to your folder:
   ```
   cd C:\path\to\your\folder
   ```
3. Run the exe:
   ```
   PDF_to_Excel_Converter.exe
   ```
4. Look for any error messages

### Step 4: Rebuild the .exe with Latest Code

Since the .exe might be old, you need to rebuild it:

1. **Copy the updated run_converter.py** from this folder to your Windows machine
2. **Install required packages**:
   ```bash
   pip install pyinstaller pandas pdfplumber openpyxl
   ```
3. **Build new .exe**:
   ```bash
   pyinstaller --onefile --name PDF_to_Excel_Converter run_converter.py
   ```
4. **Use the new .exe** from the dist folder

### Step 5: Alternative - Use GUI Version

Try building the GUI version which shows a progress window:
```bash
pyinstaller --onefile --name PDF_to_Excel_Converter --windowed pdf_to_excel_converter.py
```

### Step 6: Create a Debug Version

Create this test script as `test_exe.py`:
```python
import os
import sys
import time

print("PDF to Excel Converter - Debug Mode")
print(f"Current directory: {os.getcwd()}")
print(f"Executable location: {sys.executable}")

# Check for folders
if os.path.exists('Convert'):
    print("✓ Convert folder found")
    for subdir in ['amex', 'chase', 'w2', 'other']:
        path = os.path.join('Convert', subdir)
        if os.path.exists(path):
            pdfs = [f for f in os.listdir(path) if f.lower().endswith('.pdf')]
            print(f"  - {subdir}/: {len(pdfs)} PDFs")
else:
    print("✗ Convert folder NOT found")

if os.path.exists('Excel'):
    print("✓ Excel folder found")
else:
    print("✗ Excel folder NOT found")

print("\nPress Enter to exit...")
input()
```

Build this as:
```bash
pyinstaller --onefile --name PDF_Converter_Test test_exe.py
```

## Quick Fix - Portable Script

If the .exe continues to have issues, create a batch file `run_converter.bat`:
```batch
@echo off
python run_converter.py
pause
```

Place this in the same folder as run_converter.py and double-click to run.

## Most Likely Issue

**The .exe you're using was built before we added the W2 support and validation features.** You need to:
1. Copy the updated `run_converter.py` to Windows
2. Rebuild the .exe with PyInstaller
3. Use the new .exe file