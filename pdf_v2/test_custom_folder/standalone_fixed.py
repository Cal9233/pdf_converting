#!/usr/bin/env python3
"""
Fixed Complete Standalone PDF to Excel Converter with GUI
Fixes W2 and AmEx parsing issues
"""

import os
import sys
import tkinter as tk
from tkinter import ttk
import threading
import time
import pandas as pd
import pdfplumber
import re
from datetime import datetime
from abc import ABC, abstractmethod

# Configuration
VALID_CARDHOLDERS = {
    'LUIS RODRIGUEZ',
    'JOSE RODRIGUEZ', 
    'ISABEL RODRIGUEZ',
    'GABRIEL TRUJILLO',
    'OCOMAR ENTERPRISES',
    'JUAN LUIS RODRIGUEZ',
    'PULAK UNG',
    'RODRIGUEZ GUTIERREZ'
}

BUSINESS_INDICATORS = [
    'AIRLINES', 'AIRLINE', 'AIRWAYS', 'AIR',
    'CARD', 'CARDS', 'GIFT',
    'MERCHANDISE', 'GENERAL',
    'STORES', 'STORE', 'DISCOUNT',
    'VARIETY', 'RETAIL'
]

# Base Parser Class
class BaseParser(ABC):
    """Base parser for PDF processing"""
    
    def __init__(self):
        self.valid_cardholders = VALID_CARDHOLDERS
        self.business_indicators = BUSINESS_INDICATORS
    
    @abstractmethod
    def parse_pdf(self, pdf_path):
        """Parse PDF and return transactions"""
        pass
    
    def extract_cardholder_name(self, text):
        """Extract and validate cardholder name"""
        text = text.strip()
        
        if text in self.valid_cardholders:
            return text
        
        upper_text = text.upper()
        for indicator in self.business_indicators:
            if indicator in upper_text:
                return None
        
        words = text.split()
        if len(words) >= 2 and all(word.replace('-', '').isalpha() for word in words):
            if text.upper() in self.valid_cardholders:
                return text.upper()
        
        return None

# AmEx Parser
class AmexParser(BaseParser):
    """Parser for American Express statements"""
    
    def parse_pdf(self, pdf_path):
        transactions = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                
                # AmEx transactions can start with MM/DD/YY or MM/DD
                for i, line in enumerate(lines):
                    # Try both date patterns
                    date_match = re.match(r'^(\d{2}/\d{2}(?:/\d{2})?)', line)
                    if date_match:
                        parts = line.split()
                        if len(parts) >= 2:  # Reduced from 3 to handle shorter lines
                            date = date_match.group(1)
                            
                            # Find amount - look for pattern like $XXX.XX or XXX.XX
                            amount = None
                            amount_pattern = r'\$?([\d,]+\.\d{2})'
                            amount_matches = re.findall(amount_pattern, line)
                            if amount_matches:
                                amount = amount_matches[-1]  # Take the last amount (usually the charge)
                            
                            if amount:
                                # Extract description
                                amount_with_dollar = f'${amount}' if '$' not in line else amount
                                amount_index = line.rfind(amount)
                                date_end = line.find(date) + len(date)
                                description = line[date_end:amount_index].strip()
                                description = description.strip('$ ')
                                
                                # Look for cardholder name in surrounding lines
                                cardholder = None
                                search_range = range(max(0, i-2), min(len(lines), i+4))
                                for j in search_range:
                                    potential_name = self.extract_cardholder_name(lines[j])
                                    if potential_name:
                                        cardholder = potential_name
                                        break
                                
                                # If we have description and cardholder, add transaction
                                if cardholder and description:
                                    transactions.append({
                                        'Date': date,
                                        'Description': description,
                                        'Amount': amount,
                                        'Cardholder': cardholder
                                    })
        
        return transactions

# Chase Parser
class ChaseParser(BaseParser):
    """Parser for Chase statements"""
    
    def parse_pdf(self, pdf_path):
        transactions = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                
                for i, line in enumerate(lines):
                    date_match = re.match(r'^(\d{2}/\d{2})', line)
                    if date_match:
                        date = date_match.group(1)
                        
                        amount_match = re.search(r'([\d,]+\.\d{2})$', line)
                        if amount_match:
                            amount = amount_match.group(1)
                            
                            date_end = line.find(date) + len(date)
                            amount_start = line.rfind(amount)
                            description = line[date_end:amount_start].strip()
                            
                            cardholder = None
                            for j in range(i + 1, min(i + 4, len(lines))):
                                potential_name = self.extract_cardholder_name(lines[j])
                                if potential_name:
                                    cardholder = potential_name
                                    break
                            
                            if cardholder:
                                transactions.append({
                                    'Date': date,
                                    'Description': description,
                                    'Amount': amount,
                                    'Cardholder': cardholder
                                })
        
        return transactions

# Main Converter Class
class StandalonePDFConverter:
    """Main converter with all functionality"""
    
    def __init__(self):
        # Use simple relative paths like original program
        self.input_dir = 'Convert'
        self.output_dir = 'Excel'
        self.validation_errors = []
        
        # Create directories
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        for subfolder in ['amex', 'chase', 'other', 'w2']:
            os.makedirs(os.path.join(self.input_dir, subfolder), exist_ok=True)
    
    def _count_pdfs(self):
        """Count total PDF files"""
        count = 0
        for subdir in ['amex', 'chase', 'other', 'w2']:
            subdir_path = os.path.join(self.input_dir, subdir)
            if os.path.exists(subdir_path):
                count += len([f for f in os.listdir(subdir_path) if f.lower().endswith('.pdf')])
        return count
    
    def _get_subdirectories(self):
        return ['amex', 'chase', 'other', 'w2']
    
    def _find_pdf_files_in_subdir(self, subdir):
        pdf_files = []
        subdir_path = os.path.join(self.input_dir, subdir)
        if os.path.exists(subdir_path):
            for file in os.listdir(subdir_path):
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(subdir_path, file))
        return sorted(pdf_files)
    
    def _get_parser_for_subdir(self, subdir, filename):
        subdir_lower = subdir.lower()
        
        if subdir_lower == 'amex':
            return AmexParser()
        elif subdir_lower == 'chase':
            return ChaseParser()
        elif subdir_lower == 'w2':
            return 'w2'
        elif subdir_lower == 'other':
            filename_lower = filename.lower()
            if 'amex' in filename_lower or 'american express' in filename_lower:
                return AmexParser()
            elif 'chase' in filename_lower:
                return ChaseParser()
            else:
                return AmexParser()
        
        return None
    
    def _save_to_excel(self, transactions, subdir):
        """Save transactions to Excel"""
        output_file = os.path.join(self.output_dir, f'{subdir}.xlsx')
        
        df = pd.DataFrame(transactions)
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Transactions', index=False)
            
            worksheet = writer.sheets['Transactions']
            
            # Set column widths
            column_widths = {
                'A': 12,  # Date
                'B': 50,  # Description
                'C': 12,  # Amount
                'D': 25   # Cardholder
            }
            
            for col, width in column_widths.items():
                if col <= chr(65 + len(df.columns) - 1):
                    worksheet.column_dimensions[col].width = width
    
    def parse_w2_pdf(self, pdf_path):
        """Parse W2 PDF for tax information - FIXED VERSION"""
        w2_data = []
        validation_errors = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                
                # Find all SSN positions to identify W2 boundaries
                ssn_positions = []
                ssn_pattern = r'(\d{3}-\d{2}-\d{4})'
                
                for i, line in enumerate(lines):
                    if 'social security number' in line.lower():
                        # Check next few lines for SSN
                        for j in range(i + 1, min(i + 3, len(lines))):
                            ssn_match = re.search(ssn_pattern, lines[j])
                            if ssn_match:
                                ssn_positions.append((i, ssn_match.group(1)))
                                break
                
                # Process each W2 form found
                for form_idx, (ssn_line, ssn) in enumerate(ssn_positions):
                    w2_info = {
                        'Employer Name': '',
                        'Employee Name': '',
                        'Gross Salary': 0.0,
                        'Federal Tax': 0.0,
                        'SSN': ssn,
                        'Medicare': 0.0,
                        'State Witholds': 0.0,
                        'SDI': 0.0
                    }
                    
                    # Determine the boundaries of this W2 form
                    start_line = max(0, ssn_line - 15)
                    if form_idx + 1 < len(ssn_positions):
                        end_line = min(ssn_positions[form_idx + 1][0] - 10, ssn_line + 50)
                    else:
                        end_line = min(len(lines), ssn_line + 50)
                    
                    form_lines = lines[start_line:end_line]
                    
                    # Parse the form section
                    for i, line in enumerate(form_lines):
                        # Federal tax withheld (Box 2) - look for the label and value on same or next line
                        if 'federal income tax withheld' in line.lower():
                            # Extract from same line first
                            amount_match = re.search(r'([\d,]+\.?\d{0,2})(?:\s|$)', line)
                            if amount_match:
                                try:
                                    w2_info['Federal Tax'] = float(amount_match.group(1).replace(',', ''))
                                except:
                                    pass
                            # If not found, check next line
                            elif i + 1 < len(form_lines):
                                amount_match = re.search(r'([\d,]+\.?\d{0,2})', form_lines[i + 1])
                                if amount_match:
                                    try:
                                        w2_info['Federal Tax'] = float(amount_match.group(1).replace(',', ''))
                                    except:
                                        pass
                        
                        # Wages (Box 1) - look for pattern
                        if ('wages' in line.lower() and 'tips' in line.lower() and 
                            'social security wages' not in line.lower() and 
                            'medicare wages' not in line.lower()):
                            # Check same line
                            numbers = re.findall(r'([\d,]+\.?\d{0,2})', line)
                            if numbers:
                                try:
                                    w2_info['Gross Salary'] = float(numbers[0].replace(',', ''))
                                except:
                                    pass
                            # Check next line
                            elif i + 1 < len(form_lines):
                                amount_match = re.search(r'([\d,]+\.?\d{0,2})', form_lines[i + 1])
                                if amount_match:
                                    try:
                                        w2_info['Gross Salary'] = float(amount_match.group(1).replace(',', ''))
                                    except:
                                        pass
                        
                        # State wages and tax
                        if 'state wages' in line.lower() and 'state income tax' in line.lower():
                            if i + 1 < len(form_lines):
                                numbers = re.findall(r'[\d,]+\.?\d{0,2}', form_lines[i + 1])
                                if len(numbers) >= 2:
                                    try:
                                        w2_info['State Witholds'] = float(numbers[1].replace(',', ''))
                                    except:
                                        pass
                        
                        # Employer name (Box c)
                        if "employer's name" in line.lower():
                            if i + 1 < len(form_lines):
                                employer = form_lines[i + 1].strip()
                                if employer and not re.match(r'^[\d\s]+$', employer):
                                    # Clean up employer name
                                    employer = re.sub(r'\s*\d+\s*$', '', employer)  # Remove trailing numbers
                                    employer = employer.strip()
                                    if employer:
                                        w2_info['Employer Name'] = employer
                        
                        # Medicare tax (Box 6)
                        if 'medicare wages' in line.lower() and 'medicare tax' in line.lower():
                            numbers = re.findall(r'[\d,]+\.?\d{0,2}', line)
                            if len(numbers) >= 2:
                                try:
                                    w2_info['Medicare'] = float(numbers[1].replace(',', ''))
                                except:
                                    pass
                            elif i + 1 < len(form_lines):
                                numbers = re.findall(r'[\d,]+\.?\d{0,2}', form_lines[i + 1])
                                if len(numbers) >= 2:
                                    try:
                                        w2_info['Medicare'] = float(numbers[1].replace(',', ''))
                                    except:
                                        pass
                        
                        # Employee name (Box e) - FIXED: Handle multi-line names
                        if "employee's first name" in line.lower():
                            # Collect potential name parts from next lines
                            name_parts = []
                            skip_words = ['C', 'o', 'd', 'e', 'Code', 'Suff.', 'initial', 'Last', 'name']
                            
                            # Look ahead for name components
                            for j in range(i + 1, min(i + 10, len(form_lines))):
                                line_text = form_lines[j].strip()
                                
                                # Skip empty lines and single letters
                                if not line_text or len(line_text) <= 1:
                                    continue
                                
                                # Skip known non-name words
                                if line_text in skip_words:
                                    continue
                                
                                # Stop if we hit numbers or certain patterns
                                if re.match(r'^\d', line_text) or re.match(r'^[0-9\s]+$', line_text):
                                    break
                                
                                # Stop if we hit another field label
                                if any(label in line_text.lower() for label in ['statutory', 'retirement', 'employee', 'employer']):
                                    break
                                
                                # Add valid name parts
                                if len(line_text) > 1 and re.match(r'^[A-Za-z]', line_text):
                                    # Remove trailing single letters
                                    line_text = re.sub(r'\s+[a-z]$', '', line_text)
                                    name_parts.append(line_text)
                                    
                                    # If we have 2-3 parts, that's likely a full name
                                    if len(name_parts) >= 2:
                                        full_name = ' '.join(name_parts)
                                        # Final cleanup
                                        full_name = re.sub(r'\s+', ' ', full_name).strip()
                                        if len(full_name) > 5:  # Reasonable name length
                                            w2_info['Employee Name'] = full_name
                                            break
                    
                    # Validate and add
                    missing_fields = []
                    if not w2_info['Employee Name']:
                        missing_fields.append('Employee Name')
                    if not w2_info['Employer Name']:
                        missing_fields.append('Employer Name')
                    if w2_info['Gross Salary'] == 0:
                        missing_fields.append('Gross Salary')
                    if w2_info['Federal Tax'] == 0:
                        missing_fields.append('Federal Tax')
                    
                    if missing_fields:
                        validation_errors.append(
                            f"Page {page_num + 1}, Form {form_idx + 1} (SSN: {ssn}): Missing {', '.join(missing_fields)}"
                        )
                    
                    # Add even if some fields are missing
                    w2_data.append(w2_info)
        
        # Save validation report
        self.save_validation_report('w2', validation_errors, len(w2_data))
        
        return w2_data
    
    def save_validation_report(self, report_type, errors, total_records):
        """Save validation report to a text file"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        report_file = os.path.join(self.output_dir, 'Validation_Report.txt')
        
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
    
    def _save_w2_to_excel(self, w2_data):
        """Save W2 data to Excel"""
        output_file = os.path.join(self.output_dir, 'w2.xlsx')
        
        df = pd.DataFrame(w2_data, columns=[
            'Employer Name', 'Employee Name', 'Gross Salary', 
            'Federal Tax', 'SSN', 'Medicare', 'State Witholds', 'SDI'
        ])
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='W2_Data', index=False)
            
            worksheet = writer.sheets['W2_Data']
            widths = [30, 30, 15, 15, 15, 15, 15, 15]
            for i, width in enumerate(widths):
                worksheet.column_dimensions[chr(65 + i)].width = width
            
            for row in range(2, len(df) + 2):
                for col in ['C', 'D', 'F', 'G', 'H']:
                    worksheet[f'{col}{row}'].number_format = '$#,##0.00'

# GUI Classes
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
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        title = tk.Label(main_frame, text="PDF to Excel Converter", 
                        font=('Arial', 14, 'bold'))
        title.pack(pady=(0, 20))
        
        self.status_label = tk.Label(main_frame, text="Initializing...", 
                                   font=('Arial', 10))
        self.status_label.pack(pady=(0, 10))
        
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate',
                                      length=300)
        self.progress.pack(pady=(0, 10))
        
        self.details_label = tk.Label(main_frame, text="", 
                                    font=('Arial', 9), fg='gray')
        self.details_label.pack()
    
    def update_status(self, message):
        """Update status message"""
        self.status_label.config(text=message)
        self.root.update()
    
    def update_details(self, message):
        """Update details message"""
        self.details_label.config(text=message)
        self.root.update()
    
    def start_conversion(self):
        """Start the conversion in a separate thread"""
        self.progress.start(10)
        thread = threading.Thread(target=self.run_conversion, daemon=True)
        thread.start()
    
    def run_conversion(self):
        """Run the actual conversion"""
        try:
            converter = GUIAwarePDFConverter(self)
            
            report_file = os.path.join(converter.output_dir, 'Validation_Report.txt')
            if os.path.exists(report_file):
                os.remove(report_file)
            
            self.update_status("Looking for PDF files...")
            pdf_count = converter._count_pdfs()
            
            if pdf_count == 0:
                self.progress.stop()
                self.update_status("No PDF files found!")
                self.update_details("Place PDFs in Convert folder and try again")
                self.root.after(5000, self.root.quit)
                return
                
            self.update_status(f"Found {pdf_count} PDF files")
            time.sleep(1)
            
            self.update_status("Converting files...")
            converter.convert_all()
            
            self.progress.stop()
            self.update_status("Conversion complete!")
            
            if os.path.exists(report_file):
                self.update_details("Check Excel folder. Validation report created!")
            else:
                self.update_details("Check the Excel folder for your files")
            
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
                all_w2_data = []
                
                for pdf_file in pdf_files:
                    filename = os.path.basename(pdf_file)
                    self.gui.update_details(f"Reading: {filename}")
                    
                    try:
                        w2_data = self.parse_w2_pdf(pdf_file)
                        all_w2_data.extend(w2_data)
                    except Exception as e:
                        print(f"Error parsing W2: {e}")
                        pass
                
                if all_w2_data:
                    self.gui.update_details(f"Creating W2 Excel file...")
                    self._save_w2_to_excel(all_w2_data)
            else:
                subdir_transactions = []
                
                for i, pdf_file in enumerate(pdf_files):
                    filename = os.path.basename(pdf_file)
                    self.gui.update_details(f"Reading: {filename}")
                    
                    parser = self._get_parser_for_subdir(subdir, filename)
                    if not parser or parser == 'w2':
                        continue
                        
                    try:
                        transactions = parser.parse_pdf(pdf_file)
                        subdir_transactions.extend(transactions)
                    except Exception as e:
                        print(f"Error parsing {filename}: {e}")
                        pass
                        
                if subdir_transactions:
                    self.gui.update_details(f"Creating {subdir} Excel file...")
                    self._save_to_excel(subdir_transactions, subdir)

def main():
    """Main entry point"""
    app = SimpleProgressGUI()
    app.run()

if __name__ == "__main__":
    main()