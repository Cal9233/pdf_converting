# How to Build the PDF to Excel Converter .exe

## Prerequisites

1. **Windows Computer** - You must build the .exe on Windows (not Mac/Linux)
2. **Python 3.8 or higher** - Download from https://www.python.org/downloads/
3. **PyInstaller** - Install using pip

## Step-by-Step Instructions

### 1. Install Python (if not already installed)
- Download Python from https://www.python.org/downloads/
- During installation, CHECK "Add Python to PATH"
- Verify installation: Open Command Prompt and type `python --version`

### 2. Install Required Packages
Open Command Prompt and run:
```bash
pip install pyinstaller
pip install pandas
pip install pdfplumber
pip install openpyxl
```

### 3. Prepare the Build Directory
1. Copy the entire `pdf_v2` folder to your Windows machine
2. The folder should contain:
   - `run_converter.py` (the main program)
   - `pdf_to_excel_converter.py` (GUI version)
   - `validate_exe_build.py` (validation script)
   - `test_exe_paths.py` (path testing script)

### 4. Build the .exe
1. Open Command Prompt
2. Navigate to the pdf_usb folder:
   ```bash
   cd C:\path\to\pdf_usb
   ```
3. Run PyInstaller:
   ```bash
   pyinstaller --onefile --name PDF_to_Excel_Converter --windowed run_converter.py
   ```

### 5. Find Your .exe
After building:
- Look in the `dist` folder
- You'll find `PDF_to_Excel_Converter.exe`
- Copy this .exe back to the main pdf_usb folder

### 6. Test the .exe
1. Place some PDF files in the Convert subfolders
2. Double-click `PDF_to_Excel_Converter.exe`
3. Check the Excel folder for output files

## PyInstaller Options Explained

- `--onefile` - Creates a single .exe file (instead of many files)
- `--name PDF_to_Excel_Converter` - Names the output file
- `--windowed` - Hides the console window (GUI only)

## Alternative Build Commands

### For GUI Version (with progress bar):
```bash
pyinstaller --onefile --name PDF_to_Excel_Converter --windowed pdf_to_excel_converter.py
```

### For Console Version (shows text output):
```bash
pyinstaller --onefile --name PDF_to_Excel_Converter run_converter.py
```

### With Icon (if you have a .ico file):
```bash
pyinstaller --onefile --name PDF_to_Excel_Converter --windowed --icon=myicon.ico run_converter.py
```

## Troubleshooting

### "Module not found" errors
Make sure all required packages are installed:
```bash
pip install pandas pdfplumber openpyxl
```

### Antivirus warnings
- PyInstaller executables sometimes trigger false positives
- Add an exception in your antivirus for the .exe

### .exe crashes immediately
- Remove `--windowed` flag to see error messages
- Run from Command Prompt to see output:
  ```bash
  cd C:\path\to\folder
  PDF_to_Excel_Converter.exe
  ```

### Large file size
The .exe will be ~40-60MB because it includes:
- Python interpreter
- All required libraries
- Your code

## Distribution

To share the program:
1. Create a folder with:
   - `PDF_to_Excel_Converter.exe`
   - `Convert/` folder (with amex/, chase/, w2/, other/ subdirectories)
   - `Excel/` folder
   - `README.txt`

2. Zip the entire folder

3. Users can unzip anywhere and run the .exe

## Quick Build Script

Save this as `build.bat` in the pdf_v2 folder:
```batch
@echo off
echo Building PDF to Excel Converter...
echo.
echo Step 1: Running validation...
python validate_exe_build.py
echo.
echo Step 2: Building standalone converter...
pyinstaller --onefile --name PDF_to_Excel_Converter run_converter.py
echo.
echo Step 3: Building GUI converter...
pyinstaller --onefile --name PDF_to_Excel_Converter_GUI --windowed pdf_to_excel_converter.py
echo.
echo Step 4: Building path test tool...
pyinstaller --onefile --name test_exe_paths --windowed test_exe_paths.py
echo.
echo Build complete! Check the dist folder for:
echo - PDF_to_Excel_Converter.exe (console version)
echo - PDF_to_Excel_Converter_GUI.exe (GUI version)
echo - test_exe_paths.exe (testing tool)
pause
```

Then just double-click `build.bat` to build automatically!

## Important Notes About Paths

⚠️ **CRITICAL**: The exe looks for Convert and Excel folders in the same directory as the exe file itself.

Example working structure:
```
C:\Users\YourName\Desktop\PDF_Converter\
├── PDF_to_Excel_Converter.exe    ← Your exe here
├── Convert\                      ← Must be next to exe
│   ├── amex\                    ← Put AmEx PDFs here
│   ├── chase\                   ← Put Chase PDFs here
│   ├── other\                   ← Put other PDFs here
│   └── w2\                      ← Put W2 PDFs here
└── Excel\                        ← Output files go here
```

The exe will NOT work if:
- Convert folder is missing
- Excel folder is missing
- Folders are in the wrong location
- You run the exe from a different directory

Use `test_exe_paths.exe` to debug folder issues!