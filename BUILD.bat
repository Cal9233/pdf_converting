@echo off
title Building PDF to Excel Converter

echo Building PDF to Excel Converter...
echo.

cd pdf_v2

:: Install requirements
pip install -r requirements.txt --quiet

:: Build executable with GUI
pyinstaller --onefile --windowed --name PDF_to_Excel_Converter pdf_to_excel_converter.py

:: Deploy to USB folder
if exist "dist\PDF_to_Excel_Converter.exe" (
    cd ..
    copy "pdf_v2\dist\PDF_to_Excel_Converter.exe" "pdf_usb\"
    echo.
    echo BUILD SUCCESSFUL!
    echo Your converter is ready in: pdf_usb\
) else (
    echo.
    echo BUILD FAILED!
)

pause