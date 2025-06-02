"""
PDF to Excel Converter

A comprehensive tool for converting PDF credit card statements to Excel format.
Supports American Express and Chase statements with transaction validation
and comprehensive reporting.

Main Components:
- Core: Main converter logic and folder management
- Parsers: Statement-specific parsing for different banks
- Validators: Transaction validation and name extraction
- Exporters: Excel file creation and validation reports
- UI: Progress windows and completion dialogs
- Utils: Date utilities and text processing helpers
"""

from .core import UniversalPDFToExcelConverter

__version__ = '1.0.0'
__author__ = 'Your Name'
__email__ = 'your.email@example.com'

# Main entry point for the package
__all__ = [
    'UniversalPDFToExcelConverter'
]