# PDF to Excel Converter

Converts bank statement PDFs (AmEx and Chase) to organized Excel files with a user-friendly GUI.

## Features
- 📊 Progress bar interface
- 🔍 Automatic PDF detection
- 🏪 Clean merchant name extraction
- 📁 One Excel file per bank type
- 🚀 No Python required for end users

## Directory Structure
```
pdf_converting/
├── pdf_v2/              # Source code
│   ├── src/             # Parser modules
│   ├── config/          # Settings
│   └── Convert/         # Test PDFs
├── pdf_usb/             # Distribution folder
│   ├── Convert/         # User puts PDFs here
│   └── Excel/           # Output appears here
└── BUILD.bat            # Build script
```

## Building the Executable

### Windows:
1. Install Python 3.8+
2. Run: `BUILD.bat`
3. Find your executable in `pdf_usb/`

### Mac/Linux:
1. Install Python 3.8+
2. Run: `chmod +x build.sh && ./build.sh`
3. Or run directly: `cd pdf_v2 && python run_converter.py`

## For End Users
The `pdf_usb` folder contains everything needed:
1. Put PDFs in `Convert` subfolders:
   - AmEx → `Convert/amex/`
   - Chase → `Convert/chase/`
   - Other → `Convert/other/`
2. Run `PDF_to_Excel_Converter.exe`
3. Get Excel files from `Excel` folder

## Output Format
Excel files contain:
- **Name**: Cardholder name
- **Date**: Transaction date
- **Merchant**: Clean business name  
- **Amount**: Transaction amount

## Supported Banks
- ✅ American Express (AmEx)
- ✅ Chase
- ✅ Other (auto-detected)