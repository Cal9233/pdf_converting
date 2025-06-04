#!/bin/bash
# Simple runner script for Mac/Linux

echo "PDF to Excel Converter"
echo "====================="
echo

# Check if we're in the right directory
if [ ! -d "pdf_v2" ]; then
    echo "Error: pdf_v2 directory not found!"
    echo "Make sure you're in the pdf_converting directory"
    exit 1
fi

# Run the converter
cd pdf_v2
python pdf_to_excel_converter.py