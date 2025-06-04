#!/bin/bash
# Build script for Mac/Linux

echo "Building PDF to Excel Converter..."
echo

# Navigate to pdf_v2 directory
cd pdf_v2

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Build executable
echo "Building executable..."
pyinstaller --onefile --windowed --name PDF_to_Excel_Converter pdf_to_excel_converter.py

# Check if build succeeded
if [ -f "dist/PDF_to_Excel_Converter" ]; then
    # Copy to pdf_usb
    cd ..
    cp pdf_v2/dist/PDF_to_Excel_Converter pdf_usb/
    echo
    echo "BUILD SUCCESSFUL!"
    echo "Your converter is ready in: pdf_usb/"
else
    echo
    echo "BUILD FAILED!"
    echo "Try running: python pdf_v2/pdf_to_excel_converter.py"
fi