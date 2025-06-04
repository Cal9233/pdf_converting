"""Main PDF to Excel converter."""

import os
from datetime import datetime
from typing import List, Dict
import pandas as pd

from src.amex_parser import AmexParser
from src.chase_parser import ChaseParser
from config.settings import EXCEL_COLUMN_WIDTHS
import pdfplumber
import re


class PDFConverter:
    """Convert PDF bank statements to Excel."""
    
    def __init__(self, input_dir: str = 'data', output_dir: str = 'output'):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.validation_errors = []
        
        # Create directories if they don't exist
        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
    def convert_all(self):
        """Convert all PDFs in the input directory, creating one Excel file per subdirectory."""
        # Get subdirectories in data folder
        subdirs = self._get_subdirectories()
        
        if not subdirs:
            print("No subdirectories found in the input directory.")
            return
            
        total_files_processed = 0
        
        for subdir in subdirs:
            print(f"\n{'='*60}")
            print(f"Processing {subdir.upper()} statements...")
            print(f"{'='*60}")
            
            # Find PDFs in this subdirectory
            pdf_files = self._find_pdf_files_in_subdir(subdir)
            
            if not pdf_files:
                print(f"No PDF files found in {subdir}/ directory.")
                continue
                
            if subdir == 'w2':
                # Handle W2 files differently
                all_w2_data = []
                
                for pdf_file in pdf_files:
                    print(f"\nProcessing: {pdf_file}")
                    
                    try:
                        w2_data = self.parse_w2_pdf(pdf_file)
                        print(f"  ✓ Extracted {len(w2_data)} W-2 forms")
                        all_w2_data.extend(w2_data)
                        total_files_processed += 1
                    except Exception as e:
                        print(f"  ✗ Error parsing {pdf_file}: {str(e)}")
                
                if all_w2_data:
                    self._save_w2_to_excel(all_w2_data)
                else:
                    print(f"\nNo W-2 forms found in {subdir}/ to export.")
            else:
                # Handle regular transaction files
                subdir_transactions = []
                
                for pdf_file in pdf_files:
                    print(f"\nProcessing: {pdf_file}")
                    
                    # Determine parser based on subdirectory name
                    parser = self._get_parser_for_subdir(subdir, pdf_file)
                    if not parser:
                        print(f"  ⚠️  Could not determine parser for: {pdf_file}")
                        continue
                        
                    # Parse the PDF
                    try:
                        transactions = parser.parse_pdf(pdf_file)
                        print(f"  ✓ Extracted {len(transactions)} transactions")
                        subdir_transactions.extend(transactions)
                        total_files_processed += 1
                    except Exception as e:
                        print(f"  ✗ Error parsing {pdf_file}: {str(e)}")
                        
                # Save to Excel for this subdirectory
                if subdir_transactions:
                    self._save_to_excel(subdir_transactions, subdir)
                else:
                    print(f"\nNo transactions found in {subdir}/ to export.")
                
        if total_files_processed == 0:
            print("\nNo PDF files were successfully processed.")
        else:
            print(f"\n{'='*60}")
            print(f"Total files processed: {total_files_processed}")
    
    def _get_subdirectories(self) -> List[str]:
        """Get all subdirectories in the input directory."""
        subdirs = []
        
        if os.path.exists(self.input_dir):
            for item in os.listdir(self.input_dir):
                path = os.path.join(self.input_dir, item)
                if os.path.isdir(path):
                    subdirs.append(item)
                    
        return sorted(subdirs)
    
    def _find_pdf_files_in_subdir(self, subdir: str) -> List[str]:
        """Find all PDF files in a specific subdirectory."""
        pdf_files = []
        subdir_path = os.path.join(self.input_dir, subdir)
        
        if os.path.exists(subdir_path):
            for file in os.listdir(subdir_path):
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(subdir_path, file))
                    
        return sorted(pdf_files)
    
    def _get_parser_for_subdir(self, subdir: str, filename: str):
        """Get the appropriate parser based on subdirectory name."""
        subdir_lower = subdir.lower()
        
        if subdir_lower == 'amex':
            return AmexParser()
        elif subdir_lower == 'chase':
            return ChaseParser()
        elif subdir_lower == 'other':
            # For 'other' directory, try to determine from filename
            filename_lower = filename.lower()
            if 'amex' in filename_lower or 'american express' in filename_lower:
                return AmexParser()
            elif 'chase' in filename_lower:
                return ChaseParser()
            else:
                # Default to AmexParser for now (we'll create a generic parser later)
                print(f"  ℹ️  Using AmEx parser as default for: {filename}")
                return AmexParser()
        
        return None
    
    def _save_to_excel(self, transactions: List[Dict[str, str]], subdir: str):
        """Save transactions to Excel file with subdirectory name."""
        # Convert to DataFrame
        df = pd.DataFrame(transactions)
        
        # Ensure columns are in the right order
        df = df[['Name', 'Date', 'Merchant', 'Amount']]
        
        # Sort by Name and Date
        df = df.sort_values(['Name', 'Date'])
        
        # Use fixed filename without timestamp (lowercase)
        output_file = os.path.join(self.output_dir, f'{subdir.lower()}.xlsx')
        
        # Create Excel writer
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Transactions', index=False)
            
            # Format the worksheet
            worksheet = writer.sheets['Transactions']
            
            # Set column widths
            for col, width in EXCEL_COLUMN_WIDTHS.items():
                col_letter = chr(65 + list(EXCEL_COLUMN_WIDTHS.keys()).index(col))
                worksheet.column_dimensions[col_letter].width = width
                
            # Format amount column as currency
            for row in range(2, len(df) + 2):
                worksheet[f'D{row}'].number_format = '$#,##0.00'
                
        print(f"\n✅ Exported {len(df)} transactions to: {output_file}")
        
        # Print summary
        print(f"\nSummary for {subdir.upper()}:")
        summary = df.groupby('Name').agg({
            'Amount': ['count', 'sum']
        }).round(2)
        summary.columns = ['Transaction Count', 'Total Amount']
        print(summary.to_string())
    
    def parse_w2_pdf(self, pdf_path):
        """Parse W2 PDF for tax information."""
        w2_data = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                
                # Look for W-2 form markers
                if not any(marker in text for marker in ['OMB No. 1545-0008', 'social security number']):
                    continue
                
                # Initialize data for this W2
                w2_info = {
                    'Employer Name': '',
                    'Employee Name': '',
                    'Gross Salary': 0.0,
                    'Federal Tax': 0.0,
                    'SSN': '',
                    'Medicare': 0.0,
                    'State Witholds': 0.0,
                    'SDI': 0.0
                }
                
                lines = text.split('\n')
                
                # Parse based on the specific format we see
                for i, line in enumerate(lines):
                    # SSN appears on line after "Employee's social security number"
                    if i == 1 and 'VOID' in line:
                        ssn_match = re.search(r'(\d{3}-\d{2}-\d{4})', line)
                        if ssn_match:
                            w2_info['SSN'] = ssn_match.group(1)
                    
                    # Line 4: EIN, Wages, Federal tax
                    if i == 4:
                        # Split the line to get values more accurately
                        parts = line.split()
                        if len(parts) >= 3:
                            # First is EIN, second is wages, third is federal tax
                            try:
                                w2_info['Gross Salary'] = float(parts[1].replace(',', ''))
                                w2_info['Federal Tax'] = float(parts[2].replace(',', ''))
                            except:
                                pass
                    
                    # Line 6: Employer name
                    if i == 6:
                        w2_info['Employer Name'] = line.split()[0] + ' ' + line.split()[1] + ' ' + line.split()[2] if len(line.split()) >= 3 else line.strip()
                    
                    # Line 9: Medicare wages and tax
                    if i == 9:
                        amounts = re.findall(r'[\d,]+\.?\d{0,2}', line)
                        if len(amounts) >= 2:
                            w2_info['Medicare'] = float(amounts[1].replace(',', ''))
                    
                    # Employee name - appears around line 17
                    if i == 17 and line.strip() and not any(char.isdigit() for char in line[:3]):
                        # Remove trailing 'e' if it's just a single character
                        name = line.strip()
                        if name.endswith(' e'):
                            name = name[:-2]
                        w2_info['Employee Name'] = name
                    
                    # SDI - look for "CA SDI" pattern
                    if 'CA SDI' in line or 'SDI' in line:
                        amounts = re.findall(r'[\d,]+\.?\d{0,2}', line)
                        if amounts:
                            w2_info['SDI'] = float(amounts[0].replace(',', ''))
                    
                    # State tax - look for state patterns
                    if 'state wages' in line.lower() or 'state income tax' in line.lower():
                        if i + 1 < len(lines):
                            next_line = lines[i + 1]
                            amounts = re.findall(r'[\d,]+\.?\d{0,2}', next_line)
                            if amounts and len(amounts) >= 2:
                                try:
                                    w2_info['State Witholds'] = float(amounts[1].replace(',', ''))
                                except:
                                    pass
                
                # State tax might be in box 17 area - check lines near the end
                if w2_info['State Witholds'] == 0.0:
                    for i in range(len(lines) - 10, len(lines)):
                        if i >= 0 and i < len(lines):
                            line = lines[i]
                            if '17' in line and 'state income tax' in line.lower():
                                amounts = re.findall(r'[\d,]+\.?\d{0,2}', line)
                                if amounts:
                                    for amount in amounts:
                                        val = float(amount.replace(',', ''))
                                        if val > 0 and val < w2_info['Gross Salary']:
                                            w2_info['State Witholds'] = val
                                            break
                
                # Only add if we found valid data
                if w2_info['SSN'] and w2_info['Gross Salary'] > 0:
                    w2_data.append(w2_info)
        
        return w2_data
    
    def _save_w2_to_excel(self, w2_data: list):
        """Save W2 data to Excel."""
        df = pd.DataFrame(w2_data)
        df = df[['Employer Name', 'Employee Name', 'Gross Salary', 'Federal Tax', 
                'SSN', 'Medicare', 'State Witholds', 'SDI']]
        
        # Use fixed filename without timestamp (lowercase)
        output_file = os.path.join(self.output_dir, 'w2.xlsx')
        
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
        
        print(f"\n✅ Exported {len(df)} W-2 forms to: {output_file}")
    
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