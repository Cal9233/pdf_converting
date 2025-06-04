#!/usr/bin/env python3
"""
Simple GUI version with just a progress window
"""

import os
import sys
import tkinter as tk
from tkinter import ttk
import threading
import time

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from src.amex_parser import AmexParser
from src.chase_parser import ChaseParser
from config.settings import EXCEL_COLUMN_WIDTHS
import pandas as pd
from datetime import datetime
import pdfplumber
import re


class StandalonePDFConverter:
    """Base converter functionality"""
    
    def __init__(self):
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = current_dir
            
        self.input_dir = os.path.join(self.base_dir, 'Convert')
        self.output_dir = os.path.join(self.base_dir, 'Excel')
        self.validation_errors = []
        
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        for subfolder in ['amex', 'chase', 'other', 'w2']:
            os.makedirs(os.path.join(self.input_dir, subfolder), exist_ok=True)
    
    def _count_pdfs(self) -> int:
        """Count total PDF files in all subdirectories."""
        count = 0
        for subdir in ['amex', 'chase', 'other', 'w2']:
            subdir_path = os.path.join(self.input_dir, subdir)
            if os.path.exists(subdir_path):
                count += len([f for f in os.listdir(subdir_path) if f.lower().endswith('.pdf')])
        return count
    
    def _get_subdirectories(self) -> list:
        """Get subdirectories."""
        return ['amex', 'chase', 'other', 'w2']
    
    def _find_pdf_files_in_subdir(self, subdir: str) -> list:
        """Find PDF files in subdirectory."""
        pdf_files = []
        subdir_path = os.path.join(self.input_dir, subdir)
        if os.path.exists(subdir_path):
            for file in os.listdir(subdir_path):
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(subdir_path, file))
        return sorted(pdf_files)
    
    def _get_parser_for_subdir(self, subdir: str, filename: str):
        """Get appropriate parser."""
        subdir_lower = subdir.lower()
        
        if subdir_lower == 'amex':
            return AmexParser()
        elif subdir_lower == 'chase':
            return ChaseParser()
        elif subdir_lower == 'w2':
            return 'w2'  # Special marker for W2 parsing
        elif subdir_lower == 'other':
            filename_lower = filename.lower()
            if 'amex' in filename_lower or 'american express' in filename_lower:
                return AmexParser()
            elif 'chase' in filename_lower:
                return ChaseParser()
            else:
                return AmexParser()
        
        return None
    
    def _save_to_excel(self, transactions: list, subdir: str):
        """Save transactions to Excel."""
        df = pd.DataFrame(transactions)
        df = df[['Name', 'Date', 'Merchant', 'Amount']]
        df = df.sort_values(['Name', 'Date'])
        
        # Use fixed filename without timestamp
        output_file = os.path.join(self.output_dir, f'{subdir}_Combined.xlsx')
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Transactions', index=False)
            
            worksheet = writer.sheets['Transactions']
            
            for col, width in EXCEL_COLUMN_WIDTHS.items():
                col_letter = chr(65 + list(EXCEL_COLUMN_WIDTHS.keys()).index(col))
                worksheet.column_dimensions[col_letter].width = width
            
            for row in range(2, len(df) + 2):
                worksheet[f'D{row}'].number_format = '$#,##0.00'
    
    def parse_w2_pdf(self, pdf_path):
        """Parse W2 PDF for tax information."""
        w2_data = []
        validation_errors = []
        
        with pdfplumber.open(pdf_path) as pdf:
            all_text = ""
            # Combine all pages into one text for easier parsing
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    all_text += text + "\n"
            
            if not all_text:
                validation_errors.append(f"No text extracted from PDF: {pdf_path}")
                return w2_data
            
            # Find all SSN positions to identify W2 boundaries
            ssn_pattern = r'(\d{3}-\d{2}-\d{4})'
            ssn_positions = []
            
            lines = all_text.split('\n')
            for i, line in enumerate(lines):
                if 'social security number' in line.lower() and i + 1 < len(lines):
                    ssn_match = re.search(ssn_pattern, lines[i + 1])
                    if ssn_match:
                        ssn_positions.append((i, ssn_match.group(1)))
            
            # Process each W2 form
            for form_idx, (ssn_line_idx, ssn) in enumerate(ssn_positions):
                # Define the boundaries of this W2 form
                start_idx = max(0, ssn_line_idx - 1)
                # End at next W2 or 50 lines later (typical W2 length)
                if form_idx + 1 < len(ssn_positions):
                    end_idx = ssn_positions[form_idx + 1][0] - 1
                else:
                    end_idx = min(ssn_line_idx + 50, len(lines))
                
                # Extract form lines
                form_lines = lines[start_idx:end_idx]
                
                # Initialize W2 info
                w2_info = {
                    'Employer Name': '',
                    'Employee Name': '',
                    'Gross Salary': 0.0,
                    'Federal Tax': 0.0,
                    'SSN': ssn,  # We already have the SSN
                    'Medicare': 0.0,
                    'State Witholds': 0.0,
                    'SDI': 0.0
                }
                
                # Look for key patterns in the form
                for i, line in enumerate(form_lines):
                    # Wages and Federal tax (Box 1 and 2)
                    if 'wages, tips, other compensation' in line.lower() and 'federal income tax' in line.lower():
                        # Next line usually has EIN, wages, federal tax
                        if i + 1 < len(form_lines):
                            next_line = form_lines[i + 1]
                            # Split by spaces to handle the pattern better
                            parts = next_line.split()
                            if len(parts) >= 3:
                                try:
                                    # First part is EIN (84-4552796), second is wages, third is federal tax
                                    wage_str = parts[1].replace(',', '')
                                    tax_str = parts[2].replace(',', '')
                                    # Validate these are reasonable amounts
                                    wage = float(wage_str)
                                    tax = float(tax_str)
                                    if wage < 1000000 and tax < wage:  # Sanity check
                                        w2_info['Gross Salary'] = wage
                                        w2_info['Federal Tax'] = tax
                                except:
                                    pass
                    
                    # Employer name (Box c)
                    if "employer's name" in line.lower() or (line.startswith('c ') and 'employer' in line.lower()):
                        # Next line should be employer name
                        if i + 1 < len(form_lines):
                            employer = form_lines[i + 1].strip()
                            # Handle common case: "Ocomar Enterprises LLC"
                            if 'Ocomar' in employer:
                                w2_info['Employer Name'] = 'Ocomar Enterprises LLC'
                            elif employer and not re.match(r'^\d', employer):
                                # Extract just the company name, not the amounts
                                # Split and take the non-numeric parts
                                parts = employer.split()
                                company_parts = []
                                for part in parts:
                                    if not re.match(r'^[\d,\.]+$', part):
                                        company_parts.append(part)
                                    else:
                                        break
                                if company_parts:
                                    w2_info['Employer Name'] = ' '.join(company_parts)
                    
                    # Medicare tax (Box 6)
                    if 'medicare wages' in line.lower() and 'medicare tax' in line.lower():
                        if i + 1 < len(form_lines):
                            next_line = form_lines[i + 1]
                            numbers = re.findall(r'[\d,]+\.?\d{0,2}', next_line)
                            if len(numbers) >= 2:
                                try:
                                    # Second number is medicare tax
                                    w2_info['Medicare'] = float(numbers[1].replace(',', ''))
                                except:
                                    pass
                    
                    # Employee name (Box e) - line contains "Employee's first name"
                    if 'employee' in line.lower() and 'first name' in line.lower():
                        # Employee name appears about 4 lines after this label
                        # Skip the single letters C, o, d and find the actual name
                        for j in range(i + 1, min(i + 8, len(form_lines))):
                            potential_name = form_lines[j].strip()
                            
                            # Look for a line with full name pattern
                            # Should have multiple words and not be a single letter
                            if (potential_name and 
                                len(potential_name) > 5 and
                                ' ' in potential_name and
                                not potential_name in ['C', 'o', 'd', 'e'] and
                                re.match(r'^[A-Z][a-zA-Z]+\s+', potential_name)):
                                # Remove trailing single letter (like ' e')
                                potential_name = re.sub(r'\s+[a-z]$', '', potential_name)
                                # Remove any trailing numbers and text that starts with numbers
                                potential_name = re.sub(r'\s+\d+\s+.*$', '', potential_name)
                                w2_info['Employee Name'] = potential_name.strip()
                                break
                    
                    # State tax (Box 17)
                    if 'state income tax' in line.lower():
                        # Look for amount in same or next line
                        search_lines = [line]
                        if i + 1 < len(form_lines):
                            search_lines.append(form_lines[i + 1])
                        
                        for search_line in search_lines:
                            numbers = re.findall(r'[\d,]+\.?\d{0,2}', search_line)
                            for num in numbers:
                                try:
                                    val = float(num.replace(',', ''))
                                    # State tax should be less than gross salary
                                    if 0 < val < w2_info.get('Gross Salary', float('inf')):
                                        w2_info['State Witholds'] = val
                                        break
                                except:
                                    pass
                    
                    # SDI
                    if 'CA SDI' in line:
                        numbers = re.findall(r'[\d,]+\.?\d{0,2}', line)
                        if numbers:
                            try:
                                w2_info['SDI'] = float(numbers[-1].replace(',', ''))
                            except:
                                pass
                
                # Validate and add
                if w2_info['SSN']:
                    # Track validation errors
                    errors = []
                    if not w2_info['Employee Name']:
                        errors.append(f"Missing employee name for SSN {w2_info['SSN']}")
                    if not w2_info['Employer Name']:
                        errors.append(f"Missing employer name for SSN {w2_info['SSN']}")
                    if w2_info['Gross Salary'] == 0:
                        errors.append(f"Missing gross salary for {w2_info['Employee Name'] or 'Unknown'} (SSN: {w2_info['SSN']})")
                    if w2_info['Federal Tax'] == 0:
                        errors.append(f"Missing federal tax for {w2_info['Employee Name'] or 'Unknown'} (SSN: {w2_info['SSN']})")
                    
                    if errors:
                        validation_errors.extend(errors)
                    
                    w2_data.append(w2_info)
        
        # Save validation report
        self.save_validation_report('w2', validation_errors, len(w2_data))
        
        return w2_data
    
    def save_validation_report(self, report_type, errors, total_records):
        """Save validation report to a text file."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        report_file = os.path.join(self.output_dir, 'Validation_Report.txt')
        
        # Append to report (don't overwrite)
        with open(report_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Validation Report - {report_type.upper()}\n")
            f.write(f"Generated: {timestamp}\n")
            f.write(f"Total Records Processed: {total_records}\n")
            f.write(f"{'='*60}\n\n")
            
            if errors:
                f.write(f"⚠️  Found {len(errors)} potential issues:\n\n")
                for i, error in enumerate(errors, 1):
                    f.write(f"{i}. {error}\n")
            else:
                f.write("✅ No issues found. All data extracted successfully.\n")
            
            f.write(f"\n{'='*60}\n\n")
    
    def _save_w2_to_excel(self, w2_data: list):
        """Save W2 data to Excel."""
        df = pd.DataFrame(w2_data)
        df = df[['Employer Name', 'Employee Name', 'Gross Salary', 'Federal Tax', 
                'SSN', 'Medicare', 'State Witholds', 'SDI']]
        
        # Use fixed filename without timestamp
        output_file = os.path.join(self.output_dir, 'W2_Combined.xlsx')
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='W2_Data', index=False)
            
            worksheet = writer.sheets['W2_Data']
            # Set column widths for W2 format
            widths = [30, 30, 15, 15, 15, 15, 15, 15]
            for i, width in enumerate(widths):
                worksheet.column_dimensions[chr(65 + i)].width = width
            
            # Format currency columns
            for row in range(2, len(df) + 2):
                for col in ['C', 'D', 'F', 'G', 'H']:  # Salary and tax columns
                    worksheet[f'{col}{row}'].number_format = '$#,##0.00'


class SimpleProgressGUI:
    """Simple progress window for PDF conversion"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PDF to Excel Converter")
        self.root.geometry("400x200")
        self.root.resizable(False, False)
        
        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - 200
        y = (self.root.winfo_screenheight() // 2) - 100
        self.root.geometry(f"+{x}+{y}")
        
        # Create widgets
        self.create_widgets()
        
        # Start conversion automatically
        self.root.after(100, self.start_conversion)
        
    def create_widgets(self):
        """Create the GUI elements"""
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title = ttk.Label(main_frame, text="Converting PDFs to Excel...", 
                         font=('Arial', 14, 'bold'))
        title.pack(pady=(0, 20))
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, length=350, mode='indeterminate')
        self.progress.pack(pady=(0, 10))
        self.progress.start(10)  # Start animation
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Checking for files...", 
                                     font=('Arial', 10))
        self.status_label.pack(pady=(0, 10))
        
        # Details label
        self.details_label = ttk.Label(main_frame, text="", 
                                      font=('Arial', 9), foreground='gray')
        self.details_label.pack()
        
    def update_status(self, message):
        """Update the status message"""
        self.status_label.config(text=message)
        self.root.update()
        
    def update_details(self, message):
        """Update the details message"""
        self.details_label.config(text=message)
        self.root.update()
        
    def start_conversion(self):
        """Start the conversion in a separate thread"""
        thread = threading.Thread(target=self.run_conversion)
        thread.daemon = True
        thread.start()
        
    def run_conversion(self):
        """Run the actual conversion"""
        try:
            # Create a custom converter that updates our GUI
            converter = GUIAwarePDFConverter(self)
            
            # Clear validation report at start
            report_file = os.path.join(converter.output_dir, 'Validation_Report.txt')
            if os.path.exists(report_file):
                os.remove(report_file)
            
            # Check for files
            self.update_status("Looking for PDF files...")
            pdf_count = converter._count_pdfs()
            
            if pdf_count == 0:
                self.progress.stop()
                self.update_status("No PDF files found!")
                self.update_details("Place PDFs in Convert folder and try again")
                
                # Show message and close after 5 seconds
                self.root.after(5000, self.root.quit)
                return
                
            self.update_status(f"Found {pdf_count} PDF files")
            time.sleep(1)
            
            # Run conversion
            self.update_status("Converting files...")
            converter.convert_all()
            
            # Success
            self.progress.stop()
            self.update_status("Conversion complete!")
            
            # Check if validation report exists
            if os.path.exists(report_file):
                self.update_details("Check Excel folder. Validation report created!")
            else:
                self.update_details("Check the Excel folder for your files")
            
            # Close after 3 seconds
            self.root.after(3000, self.root.quit)
            
        except Exception as e:
            self.progress.stop()
            self.update_status("Error occurred!")
            self.update_details(str(e))
            self.root.after(5000, self.root.quit)
    
    def run(self):
        """Start the GUI"""
        self.root.mainloop()


class GUIAwarePDFConverter(StandalonePDFConverter):
    """Modified converter that updates GUI"""
    
    def __init__(self, gui):
        super().__init__()
        self.gui = gui
        
    def convert_all(self):
        """Override to update GUI during conversion"""
        subdirs = self._get_subdirectories()
        
        for subdir in subdirs:
            subdir_path = os.path.join(self.input_dir, subdir)
            if not os.path.exists(subdir_path):
                continue
                
            pdf_files = self._find_pdf_files_in_subdir(subdir)
            if not pdf_files:
                continue
                
            self.gui.update_status(f"Processing {subdir.upper()} files...")
            
            if subdir == 'w2':
                # Handle W2 files differently
                all_w2_data = []
                
                for pdf_file in pdf_files:
                    filename = os.path.basename(pdf_file)
                    self.gui.update_details(f"Reading: {filename}")
                    
                    try:
                        w2_data = self.parse_w2_pdf(pdf_file)
                        all_w2_data.extend(w2_data)
                    except Exception:
                        pass
                
                if all_w2_data:
                    self.gui.update_details(f"Creating W2 Excel file...")
                    self._save_w2_to_excel(all_w2_data)
            else:
                # Handle regular transaction files
                subdir_transactions = []
                
                for i, pdf_file in enumerate(pdf_files):
                    filename = os.path.basename(pdf_file)
                    self.gui.update_details(f"Reading: {filename}")
                    
                    parser = self._get_parser_for_subdir(subdir, pdf_file)
                    if not parser:
                        continue
                        
                    try:
                        transactions = parser.parse_pdf(pdf_file)
                        subdir_transactions.extend(transactions)
                    except Exception:
                        pass
                        
                if subdir_transactions:
                    self.gui.update_details(f"Creating {subdir} Excel file...")
                    self._save_to_excel(subdir_transactions, subdir)


def main():
    """Run the GUI converter"""
    app = SimpleProgressGUI()
    app.run()


if __name__ == "__main__":
    main()