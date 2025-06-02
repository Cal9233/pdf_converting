"""
Folder management utilities for PDF to Excel Converter

This module handles folder creation and file discovery for the conversion process.
"""

import os
from config import (
    DEFAULT_CONVERT_FOLDER,    # "Convert"
    DEFAULT_EXCEL_FOLDER       # "Excel"
)


class FolderManager:
    """Handles folder creation and file discovery"""
    
    def __init__(self, convert_folder=DEFAULT_CONVERT_FOLDER, excel_folder=DEFAULT_EXCEL_FOLDER):
        """Initialize folder manager with folder paths"""
        self.convert_folder = convert_folder
        self.excel_folder = excel_folder
    
    def setup_folders(self):
        """Create the Convert and Excel folders if they don't exist"""
        try:
            if not os.path.exists(self.convert_folder):
                os.makedirs(self.convert_folder)
                print(f"📁 Created '{self.convert_folder}' folder")
                
            if not os.path.exists(self.excel_folder):
                os.makedirs(self.excel_folder)
                print(f"📁 Created '{self.excel_folder}' folder")
        except Exception as e:
            print(f"⚠️ Could not create folders: {str(e)}")

    def get_pdf_files(self):
        """Get all PDF files from the Convert folder"""
        try:
            return [f for f in os.listdir(self.convert_folder) if f.lower().endswith('.pdf')]
        except Exception:
            return []
    
    def get_convert_folder_path(self):
        """Get the path to the Convert folder"""
        return self.convert_folder
    
    def get_excel_folder_path(self):
        """Get the path to the Excel folder"""
        return self.excel_folder