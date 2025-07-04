@echo off
echo PDF to Excel Converter
echo =======================
echo.

REM Check if conda is available
conda --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Conda is not installed. Please run setup_windows.bat first.
    pause
    exit /b 1
)

REM Check if conda environment exists
conda info --envs | findstr pdf_converter >nul 2>&1
if errorlevel 1 (
    echo ERROR: Conda environment 'pdf_converter' not found.
    echo Please run setup_windows.bat first to create the environment.
    pause
    exit /b 1
)

REM Activate conda environment and run program
echo Activating conda environment...
call conda activate pdf_converter

if not errorlevel 1 (
    echo Environment activated successfully.
    echo Starting PDF converter...
    echo.
    python pdf_converter.py
) else (
    echo ERROR: Failed to activate conda environment.
    echo Try running setup_windows.bat again.
)

echo.
echo Program finished. Press any key to exit.
pause