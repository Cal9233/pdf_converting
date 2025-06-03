"""
Folder management utilities for PDF to Excel Converter

This module handles folder creation and file discovery for the conversion process.
"""

import os
# Updated import path for your project structure
from config import (
    DEFAULT_CONVERT_FOLDER,    # "Convert"
    DEFAULT_EXCEL_FOLDER,      # "Excel"
    CONVERT_FOLDER_PATH,
    EXCEL_FOLDER_PATH,
    LOGS_FOLDER_PATH,
    PDF_EXTENSIONS
)


class FolderManager:
    """Handles folder creation and file discovery using config-based paths"""
    
    def __init__(self):
        """Initialize folder manager using paths from config"""
        # Use absolute paths from config module
        self.convert_folder = str(CONVERT_FOLDER_PATH)
        self.excel_folder = str(EXCEL_FOLDER_PATH)
        self.logs_folder = str(LOGS_FOLDER_PATH)
        
        # Debug output
        print(f"🔧 FolderManager initialized:")
        print(f"   Convert folder: {self.convert_folder}")
        print(f"   Excel folder: {self.excel_folder}")
        print(f"   Logs folder: {self.logs_folder}")
    
    def setup_folders(self):
        """Create all required folders if they don't exist"""
        folders_to_create = [
            ("Convert", self.convert_folder),
            ("Excel", self.excel_folder),
            ("Logs", self.logs_folder)
        ]
        
        for folder_name, folder_path in folders_to_create:
            try:
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path, exist_ok=True)
                    print(f"📁 Created '{folder_name}' folder at: {folder_path}")
                else:
                    print(f"📁 Found existing '{folder_name}' folder at: {folder_path}")
                    
            except Exception as e:
                print(f"❌ Could not create '{folder_name}' folder: {e}")
                raise
        
        # Verify folders are accessible
        self._verify_folders()
    
    def _verify_folders(self):
        """Verify that all folders exist and are accessible"""
        try:
            # Check Convert folder (read access)
            if not os.path.exists(self.convert_folder):
                raise Exception(f"Convert folder does not exist: {self.convert_folder}")
            if not os.access(self.convert_folder, os.R_OK):
                raise Exception(f"Cannot read from Convert folder: {self.convert_folder}")
            
            # Check Excel folder (write access)
            if not os.path.exists(self.excel_folder):
                raise Exception(f"Excel folder does not exist: {self.excel_folder}")
            if not os.access(self.excel_folder, os.W_OK):
                raise Exception(f"Cannot write to Excel folder: {self.excel_folder}")
            
            # Check Logs folder (write access)
            if not os.path.exists(self.logs_folder):
                raise Exception(f"Logs folder does not exist: {self.logs_folder}")
            if not os.access(self.logs_folder, os.W_OK):
                raise Exception(f"Cannot write to Logs folder: {self.logs_folder}")
            
            print(f"✅ All folders verified and accessible")
            
        except Exception as e:
            print(f"❌ Folder verification failed: {e}")
            raise

    def get_pdf_files(self):
        """Get all PDF files from the Convert folder"""
        try:
            if not os.path.exists(self.convert_folder):
                print(f"❌ Convert folder does not exist: {self.convert_folder}")
                return []
            
            # Get all files with PDF extensions
            pdf_files = []
            for file in os.listdir(self.convert_folder):
                file_lower = file.lower()
                if any(file_lower.endswith(ext) for ext in PDF_EXTENSIONS):
                    pdf_files.append(file)
            
            print(f"📄 Found {len(pdf_files)} PDF files in Convert folder")
            
            if pdf_files:
                print(f"📄 PDF files: {', '.join(pdf_files)}")
            else:
                print(f"📄 No PDF files found in: {self.convert_folder}")
                print(f"📄 Looking for files with extensions: {PDF_EXTENSIONS}")
                
                # Show what files ARE in the folder for debugging
                try:
                    all_files = os.listdir(self.convert_folder)
                    if all_files:
                        print(f"📄 Files found in Convert folder: {', '.join(all_files)}")
                    else:
                        print(f"📄 Convert folder is empty")
                except Exception:
                    print(f"📄 Could not list files in Convert folder")
                
            return pdf_files
            
        except Exception as e:
            print(f"❌ Error reading PDF files: {e}")
            return []
    
    def get_convert_folder_path(self):
        """Get the absolute path to the Convert folder"""
        return self.convert_folder
    
    def get_excel_folder_path(self):
        """Get the absolute path to the Excel folder"""
        return self.excel_folder
    
    def get_logs_folder_path(self):
        """Get the absolute path to the Logs folder"""
        return self.logs_folder
    
    def debug_info(self):
        """Print comprehensive debug information about folder paths"""
        print("\n🔍 FolderManager Debug Info:")
        print(f"   Convert folder: {self.convert_folder}")
        print(f"   Excel folder: {self.excel_folder}")
        print(f"   Logs folder: {self.logs_folder}")
        print(f"   Convert exists: {os.path.exists(self.convert_folder)}")
        print(f"   Excel exists: {os.path.exists(self.excel_folder)}")
        print(f"   Logs exists: {os.path.exists(self.logs_folder)}")
        print(f"   Current working directory: {os.getcwd()}")
        
        # Show contents of each folder
        for folder_name, folder_path in [
            ("Convert", self.convert_folder),
            ("Excel", self.excel_folder),
            ("Logs", self.logs_folder)
        ]:
            if os.path.exists(folder_path):
                print(f"   Contents of {folder_name} folder:")
                try:
                    contents = os.listdir(folder_path)
                    if contents:
                        for item in contents:
                            item_path = os.path.join(folder_path, item)
                            if os.path.isdir(item_path):
                                print(f"     📁 {item}/")
                            else:
                                print(f"     📄 {item}")
                    else:
                        print(f"     (empty)")
                except Exception as e:
                    print(f"     ❌ Error listing contents: {e}")
            else:
                print(f"   {folder_name} folder does not exist")
        
        print()