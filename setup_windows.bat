@echo off
echo Setting up PDF Converter with Conda...
echo.

REM Check if conda is available
conda --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Conda is not installed or not in PATH
    echo Please install Miniconda or Anaconda first:
    echo   Download from: https://docs.conda.io/en/latest/miniconda.html
    pause
    exit /b 1
)

REM Check if environment already exists
conda info --envs | findstr pdf_converter >nul 2>&1
if errorlevel 1 (
    echo Creating conda environment with Python 3.11...
    conda create -n pdf_converter python=3.11 -y
    if errorlevel 1 (
        echo ERROR: Failed to create conda environment
        pause
        exit /b 1
    )
)

REM Activate environment and install packages
echo Installing required packages...
call conda activate pdf_converter

REM Install main packages via conda (better compatibility)
echo Installing core packages via conda...
conda install pandas openpyxl -y

REM Install PDF and OCR packages via pip
echo Installing PDF processing packages...
pip install pdfplumber pytesseract

REM Install tesseract OCR engine via conda-forge
echo Installing OCR engine...
conda install -c conda-forge tesseract -y

REM Verify installation
echo.
echo Verifying installation...
python -c "import pandas, pdfplumber, openpyxl, pytesseract; print('✅ All packages installed successfully!')" >nul 2>&1

if not errorlevel 1 (
    echo.
    echo 🎉 Setup complete!
    echo.
    echo To run the program:
    echo 1. Double-click run_windows.bat
    echo.
    echo The environment 'pdf_converter' has been created and is ready to use.
) else (
    echo.
    echo ⚠️  Setup completed but there may be package issues.
    echo Try running the program - it might still work.
)

echo.
pause