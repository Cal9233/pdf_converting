"""
Folder management utilities for PDF to Excel Converter

This module handles folder creation and file discovery for the conversion process.
"""

import os
from pathlib import Path
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
        
        # NEW: Define subdirectory names
        self.amex_folder = os.path.join(self.convert_folder, "amex")
        self.chase_folder = os.path.join(self.convert_folder, "chase")
        self.processed_folder = os.path.join(self.convert_folder, "processed")
        
        # Debug output
        print(f"🔧 FolderManager initialized:")
        print(f"   Convert folder: {self.convert_folder}")
        print(f"   Excel folder: {self.excel_folder}")
        print(f"   Logs folder: {self.logs_folder}")
        print(f"   AmEx folder: {self.amex_folder}")
        print(f"   Chase folder: {self.chase_folder}")
        print(f"   Processed folder: {self.processed_folder}")
    
    def setup_folders(self):
        """Create all required folders if they don't exist"""
        # UPDATED: Include the new subdirectories
        folders_to_create = [
            ("Convert", self.convert_folder),
            ("Excel", self.excel_folder),
            ("Logs", self.logs_folder),
            ("AmEx", self.amex_folder),
            ("Chase", self.chase_folder),
            ("Processed", self.processed_folder)
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
    
    # NEW: Method to get PDF files organized by type based on subdirectory
    def get_pdf_files_by_type(self):
        """
        Get PDF files organized by statement type based on subdirectory
        
        Returns:
            dict: {'amex': [files], 'chase': [files], 'unknown': [files]}
        """
        pdf_files = {
            'amex': [],
            'chase': [],
            'unknown': []
        }
        
        # Check AmEx folder
        if os.path.exists(self.amex_folder):
            for file in os.listdir(self.amex_folder):
                file_path = os.path.join(self.amex_folder, file)
                if os.path.isfile(file_path) and any(file.lower().endswith(ext) for ext in PDF_EXTENSIONS):
                    pdf_files['amex'].append({
                        'filename': file,
                        'full_path': file_path,
                        'statement_type': 'amex'
                    })
        
        # Check Chase folder
        if os.path.exists(self.chase_folder):
            for file in os.listdir(self.chase_folder):
                file_path = os.path.join(self.chase_folder, file)
                if os.path.isfile(file_path) and any(file.lower().endswith(ext) for ext in PDF_EXTENSIONS):
                    pdf_files['chase'].append({
                        'filename': file,
                        'full_path': file_path,
                        'statement_type': 'chase'
                    })
        
        # Check main Convert folder for any PDFs (these will be 'unknown')
        if os.path.exists(self.convert_folder):
            for file in os.listdir(self.convert_folder):
                file_path = os.path.join(self.convert_folder, file)
                if (os.path.isfile(file_path) and 
                    any(file.lower().endswith(ext) for ext in PDF_EXTENSIONS)):
                    
                    # Make sure we haven't already counted this file from subdirectories
                    already_counted = False
                    for file_list in pdf_files.values():
                        if any(f['filename'] == file for f in file_list):
                            already_counted = True
                            break
                    
                    if not already_counted:
                        pdf_files['unknown'].append({
                            'filename': file,
                            'full_path': file_path,
                            'statement_type': 'unknown'
                        })
        
        # Log the results
        total_files = sum(len(files) for files in pdf_files.values())
        print(f"📄 Found {total_files} PDF files total:")
        for stmt_type, files in pdf_files.items():
            if files:
                print(f"   {stmt_type.upper()}: {len(files)} files")
                for file_info in files:
                    print(f"     - {file_info['filename']}")
        
        return pdf_files
    
    # NEW: Get statement type from file path
    def get_statement_type_from_path(self, file_path):
        """Determine statement type based on file location"""
        file_path = Path(file_path)
        parent_dir = file_path.parent.name.lower()
        
        if parent_dir == 'amex':
            return 'amex'
        elif parent_dir == 'chase':
            return 'chase'
        else:
            return 'unknown'
    
    # NEW: Move file to processed folder
    def move_file_to_processed(self, file_path):
        """Move a processed file to the processed folder"""
        try:
            source_path = Path(file_path)
            processed_path = Path(self.processed_folder)
            processed_path.mkdir(parents=True, exist_ok=True)
            
            destination_path = processed_path / source_path.name
            source_path.rename(destination_path)
            print(f"📁 Moved {source_path.name} to processed folder")
            return True
        except Exception as e:
            print(f"❌ Error moving file to processed: {e}")
            return False
    
    # NEW: Helper methods to get specific folder paths
    def get_amex_folder_path(self):
        """Get the absolute path to the AmEx folder"""
        return self.amex_folder
    
    def get_chase_folder_path(self):
        """Get the absolute path to the Chase folder"""
        return self.chase_folder
    
    def get_processed_folder_path(self):
        """Get the absolute path to the processed folder"""
        return self.processed_folder
    
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
        print(f"   AmEx folder: {self.amex_folder}")
        print(f"   Chase folder: {self.chase_folder}")
        print(f"   Processed folder: {self.processed_folder}")
        print(f"   Convert exists: {os.path.exists(self.convert_folder)}")
        print(f"   Excel exists: {os.path.exists(self.excel_folder)}")
        print(f"   Logs exists: {os.path.exists(self.logs_folder)}")
        print(f"   AmEx exists: {os.path.exists(self.amex_folder)}")
        print(f"   Chase exists: {os.path.exists(self.chase_folder)}")
        print(f"   Processed exists: {os.path.exists(self.processed_folder)}")
        print(f"   Current working directory: {os.getcwd()}")
        
        # Show contents of each folder
        for folder_name, folder_path in [
            ("Convert", self.convert_folder),
            ("Excel", self.excel_folder),
            ("Logs", self.logs_folder),
            ("AmEx", self.amex_folder),
            ("Chase", self.chase_folder),
            ("Processed", self.processed_folder)
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