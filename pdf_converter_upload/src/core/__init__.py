"""
Core package for PDF to Excel Converter

This package contains the main converter logic and folder management.
The core components orchestrate the entire conversion process by coordinating
parsers, validators, exporters, and UI components.
"""

from .converter import UniversalPDFToExcelConverter
from .folder_manager import FolderManager

__all__ = [
    'UniversalPDFToExcelConverter',
    'FolderManager'
]

__version__ = '1.0.0'