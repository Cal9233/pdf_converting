PDF to Excel Converter
======================

OVERVIEW:
--------
This program converts PDF files to Excel spreadsheets with support for:
- AmEx credit card statements
- Chase credit card statements  
- W-2 tax forms
- Invoice files (including scanned/image-based PDFs with OCR)
- Other financial statements

REQUIREMENTS:
------------
- Python 3.7 or higher
- Conda (Miniconda or Anaconda)
- !!!! pip install pyinstaller !!!!!!
- Internet connection (for initial setup only)

SETUP:
------
Windows: 
  1. Install Miniconda from: https://docs.conda.io/en/latest/miniconda.html
  2. Double-click setup_windows.bat

macOS:   
  1. Install Miniconda: brew install miniconda
     OR download from: https://docs.conda.io/en/latest/miniconda.html
  2. Double-click setup_mac.sh (or run: ./setup_mac.sh in Terminal)

The setup will automatically:
- Create a conda environment called 'pdf_converter'
- Install all required packages (pandas, pdfplumber, pytesseract, etc.)
- Set up OCR capabilities for scanned documents

RUN PROGRAM:
-----------
Windows: Double-click run_windows.bat
macOS:   Double-click run_mac.sh (or run: ./run_mac.sh in Terminal)

USAGE:
------
1. Place PDF files in the appropriate Convert subfolders:
   - Convert/amex/     - AmEx credit card statements
   - Convert/chase/    - Chase credit card statements  
   - Convert/w2/       - W-2 tax forms
   - Convert/invoice/  - Invoice files (supports scanned PDFs)
   - Convert/other/    - Other financial statements

2. Run the program using the run script for your operating system

3. Excel files will be created in the Excel/ folder:
   - amex.xlsx, chase.xlsx, other.xlsx - Transaction data
   - w2.xlsx - W-2 tax information  
   - invoice.xlsx - Invoice data with two sheets:
     * Register_Summary - Overall summary
     * Individual_Invoices - Detailed line items

4. Check Validation_Report.txt for any parsing issues

FEATURES:
--------
- Automatic PDF type detection (text-based vs scanned)
- OCR support for scanned/image-based PDFs
- Multiple cardholder support for credit card statements
- Detailed validation reporting
- Cross-platform compatibility (Windows/macOS)
- Preserves original PDF order for financial records

TROUBLESHOOTING:
---------------
- If setup fails, make sure Conda is installed and in your PATH
- On macOS, you may need to allow scripts to run in System Preferences > Security & Privacy
- If you get permission errors on macOS, run: chmod +x *.sh
- For OCR issues, ensure tesseract is properly installed via the setup script
- Check Validation_Report.txt for specific parsing errors

SUPPORTED FILE TYPES:
--------------------
- Text-based PDFs (preferred - faster processing)
- Scanned/image-based PDFs (requires OCR - slower but works)
- Multi-page documents
- Various PDF formats and layouts

For questions or issues, check the validation report first as it provides
detailed information about any parsing problems encountered.