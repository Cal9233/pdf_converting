#!/bin/bash
echo "PDF to Excel Converter"
echo "======================"
echo

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "ERROR: Conda is not installed. Please run setup_mac.sh first."
    read -p "Press any key to exit..."
    exit 1
fi

# Check if conda environment exists
if ! conda info --envs | grep -q pdf_converter; then
    echo "ERROR: Conda environment 'pdf_converter' not found."
    echo "Please run setup_mac.sh first to create the environment."
    read -p "Press any key to exit..."
    exit 1
fi

# Activate conda environment and run program
echo "Activating conda environment..."
eval "$(conda shell.bash hook)"
conda activate pdf_converter

if [ $? -eq 0 ]; then
    echo "Environment activated successfully."
    echo "Starting PDF converter..."
    echo
    python pdf_converter.py
else
    echo "ERROR: Failed to activate conda environment."
    echo "Try running setup_mac.sh again."
fi

echo
echo "Program finished. Press any key to exit."
read -p "Press any key to continue..."