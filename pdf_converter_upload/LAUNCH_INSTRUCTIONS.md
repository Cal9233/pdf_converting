# PDF to Excel Converter - Launch Instructions

## Quick Start (For Pre-Built Executable)

If you have the `dist_final` folder:

```bash
# Navigate to the folder
cd path/to/dist_final

# Add your PDF files to the Convert folder
cp your_statement.pdf Convert/

# Run the converter
./PDF_to_Excel_Converter

# Check results in Excel folder
ls Excel/
```

---

## Development Setup (From Source Code)

### 1. Clone/Download Project

```bash
# If using git
git clone your-repo-url
cd pdf_converting

# Or if you have the source files
cd path/to/pdf_converting
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it (macOS/Linux)
source venv/bin/activate

# Activate it (Windows)
# venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install all required packages
pip install pdfplumber pandas openpyxl pyinstaller

# Or if you have requirements.txt
pip install -r requirements.txt
```

### 4. Run the Application

```bash
# Run directly from source
python run.py
```

---

## Building Your Own Executable

### 1. Setup Environment (if not done)

```bash
python3 -m venv venv
source venv/bin/activate
pip install pdfplumber pandas openpyxl pyinstaller
```

### 2. Build Executable

```bash
# Run the build script
python build.py
```

### 3. Test the Build

```bash
# Navigate to output folder
cd dist_final

# Add test PDF
cp test_statement.pdf Convert/

# Run executable
./PDF_to_Excel_Converter

# Check results
ls Excel/
```

---

## Cloud Server Deployment

### 1. Upload Essential Files

Upload only these folders/files:

- `src/` (all source code)
- `config/` (configuration)
- `run.py`
- `build.py`
- `requirements.txt`
- `README.md`

### 2. Setup on Server

```bash
# SSH into server
ssh user@your-server.com

# Navigate to project
cd pdf_converting

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Test application
python run.py
```

### 3. Build on Server (optional)

```bash
# If you want to create executable on server
python build.py

# The executable will be in dist_final/
```

---

## Troubleshooting

### Common Issues:

**"No module named 'pdfplumber'"**

```bash
# Make sure virtual environment is activated
source venv/bin/activate
pip install pdfplumber pandas openpyxl
```

**"externally-managed-environment" error**

```bash
# Use virtual environment instead
python3 -m venv venv
source venv/bin/activate
pip install [packages]
```

**Build fails**

```bash
# Check dependencies first
python -c "import pdfplumber, pandas, openpyxl; print('All good!')"

# Clean build
rm -rf build dist
python build.py
```

**Executable doesn't work**

```bash
# Use console mode for debugging
# In build.py, change '--windowed' to '--console'
python build.py
```

### File Permissions (macOS/Linux)

```bash
# Make executable runnable
chmod +x PDF_to_Excel_Converter
```

---

## Project Structure

```
pdf_converting/
├── run.py                    # Main launcher
├── build.py                  # Build script
├── requirements.txt          # Dependencies
├── config/                   # Settings
├── src/                      # Source code
├── Convert/                  # Input PDFs (create if missing)
├── Excel/                    # Output Excel files (create if missing)
├── logs/                     # Log files (create if missing)
└── dist_final/              # Final executable (after build)
    ├── PDF_to_Excel_Converter
    ├── Convert/
    ├── Excel/
    ├── logs/
    └── INSTRUCTIONS.txt
```

---

## Usage Notes

### Supported Files:

- ✅ American Express credit card statements (PDF)
- ✅ Chase credit card statements (PDF)

### What Gets Extracted:

- Cardholder name
- Transaction date
- Merchant name
- Transaction amount

### Output:

- Separate Excel files for AmEx and Chase
- Validation report with confidence scores
- Organized by cardholder name

### Tips:

- Put all PDFs in the `Convert` folder before running
- Results appear in the `Excel` folder
- Check validation reports for accuracy
- Console output shows progress and any issues

---

## Deactivate Virtual Environment

When done working:

```bash
deactivate
```

## Version Info

- **Built with:** Python 3.13
- **Dependencies:** pdfplumber, pandas, openpyxl
- **Platform:** Cross-platform (macOS, Linux, Windows)
- **Version:** 1.0.0
