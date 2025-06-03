"""
Main PDF to Excel converter that orchestrates the conversion process.

This module contains the main UniversalPDFToExcelConverter class that coordinates
all components (parsers, validators, exporters, UI) to convert PDF statements to Excel.
"""

import os
import time
import pdfplumber
from src.parsers import AmexParser, ChaseParser
from src.validators import TransactionValidator
from src.exporters import ExcelExporter
from src.ui import ProgressWindow
from src.core.folder_manager import FolderManager

from config.settings import (
    AMEX_KEYWORDS,           # ['AMEX', 'AMERICAN', 'AMERICAN EXPRESS', 'AMAZON BUSINESS PRIME CARD']
    CHASE_KEYWORDS           # ['CHASE', 'ULTIMATE REWARDS', 'ACCOUNT ACTIVITY']
)


class UniversalPDFToExcelConverter:
    """Main converter class that orchestrates the PDF to Excel conversion process"""
    
    def __init__(self):
        """Initialize the converter with all necessary components"""
        # Initialize all components
        self.folder_manager = FolderManager()
        self.amex_parser = AmexParser()
        self.chase_parser = ChaseParser()
        self.validator = TransactionValidator()
        self.excel_exporter = ExcelExporter(self.folder_manager.get_excel_folder_path())
        self.progress_window = ProgressWindow()
        
        # Global state for Chase date handling
        self.chase_date_range = None
    
    def run(self):
        """Main entry point for the conversion process"""
        self.progress_window.update_progress("🚀 Starting PDF processing...", "Initializing conversion process")
        start_time = time.time()
        
        try:
            # Setup folders (now includes subdirectories)
            self.folder_manager.setup_folders()
            
            # NEW: Try directory-based approach first, fallback to legacy if no files found
            pdf_files_by_type = self.folder_manager.get_pdf_files_by_type()
            total_files = sum(len(files) for files in pdf_files_by_type.values())
            
            # If no files found in subdirectories, fallback to legacy method
            if total_files == 0:
                print("📁 No files found in subdirectories, checking main Convert folder...")
                legacy_pdf_files = self.folder_manager.get_pdf_files()
                if not legacy_pdf_files:
                    self.progress_window.update_progress("❌ No PDF files found", 
                        "Add PDFs to Convert/amex/ or Convert/chase/ folders (or main Convert folder) and try again")
                    return 0, 0
                
                # Use legacy processing method
                return self._run_legacy_processing(legacy_pdf_files, start_time)
            
            # NEW: Directory-based processing
            return self._run_directory_based_processing(pdf_files_by_type, start_time)
        
        except Exception as e:
            self.progress_window.update_progress("❌ Unexpected error occurred", f"Error: {str(e)}")
            return 0, 0
    
    def _run_legacy_processing(self, pdf_files, start_time):
        """Legacy processing method for files in main Convert folder"""
        self.progress_window.update_progress(f"📁 Found {len(pdf_files)} PDF file(s)", f"Files: {', '.join(pdf_files)}", force_update=True)
        
        # Separate data by statement type
        amex_data = []
        chase_data = []
        
        # Process each PDF file using legacy method
        for i, pdf_file in enumerate(pdf_files, 1):
            try:
                pdf_path = os.path.join(self.folder_manager.get_convert_folder_path(), pdf_file)
                self.progress_window.update_progress(f"📄 Processing PDF {i}/{len(pdf_files)}", f"{pdf_file}", force_update=True)
                
                data, statement_type = self.extract_pdf_content(pdf_path)
                
                if data:
                    if statement_type == 'amex':
                        amex_data.extend(data)
                    elif statement_type == 'chase':
                        chase_data.extend(data)
                    
                    self.progress_window.update_progress(f"✅ Extracted {len(data)} transactions", "", force_update=True)
                else:
                    self.progress_window.update_progress(f"❌ Failed to extract data from {pdf_file}", "", force_update=True)
            
            except Exception as e:
                self.progress_window.update_progress(f"❌ Error processing {pdf_file}", f"Error: {str(e)}", force_update=True)
                continue
        
        return self._create_excel_files_and_finish(amex_data, chase_data, start_time)
    
    def _run_directory_based_processing(self, pdf_files_by_type, start_time):
        """NEW: Directory-based processing method"""
        total_files = sum(len(files) for files in pdf_files_by_type.values())
        
        # Display file summary
        summary = []
        for stmt_type, files in pdf_files_by_type.items():
            if files:
                summary.append(f"{stmt_type.upper()}: {len(files)}")
        
        self.progress_window.update_progress(f"📁 Found {total_files} PDF file(s)", 
            f"Files by type: {', '.join(summary)}", force_update=True)
        
        # Separate data by statement type
        amex_data = []
        chase_data = []
        
        # Process each statement type
        file_count = 0
        for statement_type, files in pdf_files_by_type.items():
            if not files:
                continue
            
            for file_info in files:
                file_count += 1
                try:
                    self.progress_window.update_progress(
                        f"📄 Processing PDF {file_count}/{total_files}", 
                        f"{file_info['filename']} ({statement_type})", force_update=True
                    )
                    
                    data, detected_type = self.extract_pdf_content_with_known_type(
                        file_info['full_path'], 
                        file_info['statement_type']
                    )
                    
                    if data:
                        if detected_type == 'amex':
                            amex_data.extend(data)
                        elif detected_type == 'chase':
                            chase_data.extend(data)
                        
                        self.progress_window.update_progress(
                            f"✅ Extracted {len(data)} transactions", "", force_update=True
                        )
                    else:
                        self.progress_window.update_progress(
                            f"❌ Failed to extract data from {file_info['filename']}", "", force_update=True
                        )
                
                except Exception as e:
                    self.progress_window.update_progress(
                        f"❌ Error processing {file_info['filename']}", f"Error: {str(e)}", force_update=True
                    )
                    continue
        
        return self._create_excel_files_and_finish(amex_data, chase_data, start_time)
    
    def _create_excel_files_and_finish(self, amex_data, chase_data, start_time):
        """Common method to create Excel files and finish processing"""
        # Create Excel files
        self.progress_window.update_progress("📈 Creating Excel files...", 
                                           f"AmEx: {len(amex_data)}, Chase: {len(chase_data)} transactions", force_update=True)
        
        files_created = 0
        
        if amex_data:
            self.progress_window.update_progress("📝 Creating AmEx Excel file...", "", force_update=True)
            success = self.excel_exporter.create_excel_file(amex_data, 'AmEx_Combined')
            if success:
                files_created += 1
        
        if chase_data:
            self.progress_window.update_progress("📝 Creating Chase Excel file...", "", force_update=True)
            success = self.excel_exporter.create_excel_file(chase_data, 'Chase_Combined')
            if success:
                files_created += 1
        
        # Generate validation report
        try:
            if hasattr(self, 'validator') and self.validator.validation_results:
                self.progress_window.update_progress("📋 Creating validation report...", "", force_update=True)
                self.excel_exporter.create_validation_report(self.validator.validation_results)
        except Exception as e:
            print(f"❌ Error creating validation report: {e}")
        
        # Calculate totals
        end_time = time.time()
        processing_time = end_time - start_time
        total_transactions = len(amex_data) + len(chase_data)
        
        self.progress_window.update_progress("🎉 Processing Complete!", 
                                           f"Files: {files_created}, Transactions: {total_transactions}", force_update=True)
        
        return files_created, total_transactions
    
    def extract_pdf_content(self, pdf_path):
        """Extract transaction data from PDF using appropriate parser (LEGACY METHOD)"""
        extracted_data = []
        statement_type = 'unknown'
        
        self.progress_window.update_progress("📄 Reading PDF content...", f"Processing: {os.path.basename(pdf_path)}", force_update=True)
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Get full text for detection and date extraction
                full_text = ""
                for page in pdf.pages:
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            full_text += page_text + "\n"
                    except Exception:
                        continue
                
                # Detect statement type using legacy method
                filename = os.path.basename(pdf_path)
                statement_type = self.detect_statement_type(full_text, filename)
                self.progress_window.update_progress(f"🔍 Detected: {statement_type} (legacy method)", "", force_update=True)
                
                # Choose appropriate parser and setup
                if statement_type == 'amex':
                    parser = self.amex_parser
                elif statement_type == 'chase':
                    parser = self.chase_parser
                    # Extract primary account holder from address on page 1
                    primary_name = parser.extract_primary_account_holder(full_text)
                    parser.primary_account_holder = primary_name
                    parser.current_cardholder = primary_name
                    # Extract date range for Chase statements
                    self.chase_date_range = parser.extract_chase_date_range(full_text)
                    # Set the date range in the parser so it can use it
                    parser.chase_date_range = self.chase_date_range
                else:
                    return None, statement_type
                
                # Extract transactions from all pages
                self.progress_window.update_progress(f"📖 Processing {len(pdf.pages)} pages...", "", force_update=True)
                
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            if page_num % 5 == 1 or page_num == len(pdf.pages):
                                self.progress_window.update_progress(f"📄 Processing page {page_num}...", "", force_update=True)
                            
                            # Use appropriate parser
                            page_transactions = parser.parse_page(page_text, page_num)
                            extracted_data.extend(page_transactions)
                    except Exception as e:
                        continue
                
                # CHASE CLEANUP: Skip final cleanup since Chase parser handles sections properly
                if statement_type == 'chase':
                    print("✅ CHASE: Skipping final cleanup - section-based parsing already assigned names correctly")
                
                # Validation step
                if extracted_data and statement_type != 'unknown':
                    self.progress_window.update_progress("🔍 Validating extraction...", "Checking for missed transactions", force_update=True)
                    validation_result = self.validator.validate_extraction(pdf_path, extracted_data, statement_type)
                    self.validator.validation_results[pdf_path] = validation_result
        
        except Exception as e:
            self.progress_window.update_progress("❌ PDF processing error", f"Error: {str(e)}")
            return None, statement_type
            
        return extracted_data, statement_type
    
    def extract_pdf_content_with_known_type(self, pdf_path, expected_statement_type):
        """NEW: Extract transaction data from PDF using directory-based type detection"""
        extracted_data = []
        
        self.progress_window.update_progress("📄 Reading PDF content...", 
            f"Processing: {os.path.basename(pdf_path)}", force_update=True)
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Get full text for validation (still needed for Chase date extraction)
                full_text = ""
                for page in pdf.pages:
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            full_text += page_text + "\n"
                    except Exception:
                        continue
                
                # Use directory-based detection instead of keyword detection
                statement_type = self.folder_manager.get_statement_type_from_path(pdf_path)
                
                # Fallback to expected type if path detection fails
                if statement_type == 'unknown':
                    statement_type = expected_statement_type
                
                self.progress_window.update_progress(f"🔍 Detected: {statement_type} (from directory)", "", force_update=True)
                
                # Choose appropriate parser and setup
                if statement_type == 'amex':
                    parser = self.amex_parser
                elif statement_type == 'chase':
                    parser = self.chase_parser
                    # Extract primary account holder from address on page 1
                    primary_name = parser.extract_primary_account_holder(full_text)
                    parser.primary_account_holder = primary_name
                    parser.current_cardholder = primary_name
                    # Extract date range for Chase statements
                    self.chase_date_range = parser.extract_chase_date_range(full_text)
                    # Set the date range in the parser so it can use it
                    parser.chase_date_range = self.chase_date_range
                else:
                    return None, statement_type
                
                # Extract transactions from all pages
                self.progress_window.update_progress(f"📖 Processing {len(pdf.pages)} pages...", "", force_update=True)
                
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            if page_num % 5 == 1 or page_num == len(pdf.pages):
                                self.progress_window.update_progress(f"📄 Processing page {page_num}...", "", force_update=True)
                            
                            # Use appropriate parser
                            page_transactions = parser.parse_page(page_text, page_num)
                            extracted_data.extend(page_transactions)
                    except Exception as e:
                        continue
                
                # CHASE CLEANUP: Skip final cleanup since Chase parser handles sections properly
                if statement_type == 'chase':
                    print("✅ CHASE: Skipping final cleanup - section-based parsing already assigned names correctly")
                
                # Validation step
                if extracted_data and statement_type != 'unknown':
                    self.progress_window.update_progress("🔍 Validating extraction...", "Checking for missed transactions", force_update=True)
                    validation_result = self.validator.validate_extraction(pdf_path, extracted_data, statement_type)
                    self.validator.validation_results[pdf_path] = validation_result
        
        except Exception as e:
            self.progress_window.update_progress("❌ PDF processing error", f"Error: {str(e)}")
            return None, statement_type
            
        return extracted_data, statement_type
    
    def detect_statement_type(self, text, filename):
        """Detect if the PDF is American Express or Chase using config keywords (LEGACY METHOD)"""
        try:
            text_upper = text.upper()
            filename_upper = filename.upper()
            
            # Check filename first for more reliable detection
            if any(keyword in filename_upper for keyword in AMEX_KEYWORDS):
                return 'amex'
            elif any(keyword in filename_upper for keyword in CHASE_KEYWORDS):
                return 'chase'
            
            # Fallback to content detection
            if any(keyword in text_upper for keyword in AMEX_KEYWORDS):
                return 'amex'
            elif any(keyword in text_upper for keyword in CHASE_KEYWORDS):
                return 'chase'
            else:
                return 'unknown'
        except Exception:
            return 'unknown'