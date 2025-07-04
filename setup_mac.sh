#!/bin/bash
echo "Setting up PDF Converter with Conda..."
echo

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "ERROR: Conda is not installed or not in PATH"
    echo "Please install Miniconda or Anaconda first:"
    echo "  brew install miniconda"
    echo "  OR download from: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

# Initialize conda if needed
if ! conda info --envs | grep -q pdf_converter; then
    echo "Creating conda environment with Python 3.11..."
    conda create -n pdf_converter python=3.11 -y
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create conda environment"
        exit 1
    fi
fi

# Activate environment and install packages
echo "Installing required packages..."
eval "$(conda shell.bash hook)"
conda activate pdf_converter

# Install main packages via conda (better compatibility)
echo "Installing core packages via conda..."
conda install pandas openpyxl -y

# Install PDF and OCR packages via pip
echo "Installing PDF processing packages..."
pip install pdfplumber pytesseract

# Install tesseract OCR engine via conda-forge
echo "Installing OCR engine..."
conda install -c conda-forge tesseract -y

# Verify installation
echo
echo "Verifying installation..."
python -c "import pandas, pdfplumber, openpyxl, pytesseract; print('✅ All packages installed successfully!')" 2>/dev/null

if [ $? -eq 0 ]; then
    echo
    echo "🎉 Setup complete!"
    echo
    echo "To run the program:"
    echo "1. Double-click run_mac.sh (or run: ./run_mac.sh)"
    echo
    echo "The environment 'pdf_converter' has been created and is ready to use."
else
    echo
    echo "⚠️  Setup completed but there may be package issues."
    echo "Try running the program - it might still work."
fi