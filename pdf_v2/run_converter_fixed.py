#!/usr/bin/env python3
"""
Fixed PDF to Excel Converter - Uses working directory like original
This version works exactly like original_program.py for folder detection
"""

import os
import sys
from datetime import datetime
import pandas as pd
import pdfplumber
import re

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

class SimplePDFConverter:
    def __init__(self):
        # Use simple relative paths like the original program
        # This makes folders relative to current working directory
        self.input_dir = 'Convert'
        self.output_dir = 'Excel'
        self.validation_errors = []
        
        # Create directories
        for dir_path in [self.input_dir, self.output_dir]:
            os.makedirs(dir_path, exist_ok=True)
        
        for subdir in ['amex', 'chase', 'other', 'w2']:
            os.makedirs(os.path.join(self.input_dir, subdir), exist_ok=True)
    
    def extract_cardholder_name(self, text):
        """Extract cardholder name if valid."""
        text = text.strip()
        if text in VALID_CARDHOLDERS:
            return text
        
        # Check if it's a business name
        upper_text = text.upper()
        for indicator in BUSINESS_INDICATORS:
            if indicator in upper_text:
                return None
        
        # If it's a potential name, validate
        words = text.split()
        if len(words) >= 2 and all(word.replace('-', '').isalpha() for word in words):
            if text.upper() in VALID_CARDHOLDERS:
                return text.upper()
        
        return None
    
    def parse_amex_pdf(self, pdf_path):
        """Parse American Express PDF."""
        transactions = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                
                for i, line in enumerate(lines):
                    # Look for date pattern
                    date_match = re.match(r'^(\d{2}/\d{2}/\d{2})', line)
                    if date_match:
                        parts = line.split()
                        if len(parts) >= 3:
                            date = parts[0]
                            
                            # Extract amount (last numeric value)
                            amount = None
                            for part in reversed(parts):
                                if re.match(r'[\d,]+\.\d{2}$', part):
                                    amount = part
                                    break
                            
                            if amount:
                                # Extract description (everything between date and amount)
                                amount_index = line.rfind(amount)
                                date_index = line.find(date) + len(date)
                                description = line[date_index:amount_index].strip()
                                
                                # Look for cardholder name in next few lines
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
    
    def parse_chase_pdf(self, pdf_path):
        """Parse Chase PDF."""
        transactions = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                
                for i, line in enumerate(lines):
                    # Look for date pattern at start of line
                    date_match = re.match(r'^(\d{2}/\d{2})', line)
                    if date_match:
                        date = date_match.group(1)
                        
                        # Find amount pattern
                        amount_match = re.search(r'([\d,]+\.\d{2})$', line)
                        if amount_match:
                            amount = amount_match.group(1)
                            
                            # Extract description
                            date_end = line.find(date) + len(date)
                            amount_start = line.rfind(amount)
                            description = line[date_end:amount_start].strip()
                            
                            # Look for cardholder
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
    
    def parse_w2_pdf(self, pdf_path):
        """Parse W2 PDF for tax information."""
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
                    if 'social security number' in line.lower() and i + 1 < len(lines):
                        ssn_match = re.search(ssn_pattern, lines[i + 1])
                        if ssn_match:
                            ssn_positions.append((i, ssn_match.group(1)))
                
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
                    start_line = max(0, ssn_line - 10)
                    if form_idx + 1 < len(ssn_positions):
                        end_line = ssn_positions[form_idx + 1][0] - 10
                    else:
                        end_line = len(lines)
                    
                    form_lines = lines[start_line:end_line]
                    
                    # Parse the form section
                    for i, line in enumerate(form_lines):
                        # Federal tax withheld (Box 2)
                        if 'federal income tax withheld' in line.lower():
                            if i + 1 < len(form_lines):
                                amount_match = re.search(r'([\d,]+\.?\d{0,2})', form_lines[i + 1])
                                if amount_match:
                                    try:
                                        w2_info['Federal Tax'] = float(amount_match.group(1).replace(',', ''))
                                    except:
                                        pass
                        
                        # Wages (Box 1)
                        if 'wages' in line.lower() and 'tips' in line.lower() and 'social security wages' not in line.lower():
                            if i + 1 < len(form_lines):
                                amount_match = re.search(r'([\d,]+\.?\d{0,2})', form_lines[i + 1])
                                if amount_match:
                                    try:
                                        w2_info['Gross Salary'] = float(amount_match.group(1).replace(',', ''))
                                    except:
                                        pass
                        
                        # State wages and tax (Boxes 16 & 17)
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
                                if 'Ocomar' in employer:
                                    w2_info['Employer Name'] = 'Ocomar Enterprises LLC'
                                elif employer and not re.match(r'^\d', employer):
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
                                        w2_info['Medicare'] = float(numbers[1].replace(',', ''))
                                    except:
                                        pass
                        
                        # Employee name (Box e)
                        if "employee's first name" in line.lower():
                            if i + 1 < len(form_lines):
                                name_line = form_lines[i + 1].strip()
                                name_parts = []
                                words = name_line.split()
                                for word in words:
                                    if word and not re.match(r'^\d', word) and len(word) > 1:
                                        if not any(char.isdigit() for char in word):
                                            name_parts.append(word)
                                        else:
                                            break
                                
                                if name_parts:
                                    full_name = ' '.join(name_parts)
                                    full_name = re.sub(r'\s+', ' ', full_name).strip()
                                    if len(full_name) > 2 and not full_name.isdigit():
                                        w2_info['Employee Name'] = full_name
                    
                    # Validate and add
                    missing_fields = []
                    if not w2_info['Employee Name']:
                        missing_fields.append('Employee Name')
                    if w2_info['Gross Salary'] == 0:
                        missing_fields.append('Gross Salary')
                    if w2_info['Federal Tax'] == 0:
                        missing_fields.append('Federal Tax')
                    
                    if missing_fields:
                        validation_errors.append(
                            f"Page {page_num + 1}, Form {form_idx + 1} (SSN: {ssn}): Missing {', '.join(missing_fields)}"
                        )
                    
                    if w2_info['Employee Name'] or w2_info['Gross Salary'] > 0:
                        w2_data.append(w2_info)
        
        # Save validation report
        self.save_validation_report('w2', validation_errors, len(w2_data))
        
        return w2_data
    
    def save_validation_report(self, report_type, errors, total_records):
        """Save validation report to a text file."""
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
    
    def convert_all(self):
        """Convert all PDFs in subdirectories."""
        print("\n🔄 Starting PDF to Excel conversion...")
        print(f"📁 Looking in: {os.path.abspath(self.input_dir)}")
        
        # Clear old validation report
        report_file = os.path.join(self.output_dir, 'Validation_Report.txt')
        if os.path.exists(report_file):
            os.remove(report_file)
        
        total_files = 0
        subdirs = ['amex', 'chase', 'other', 'w2']
        
        for subdir in subdirs:
            subdir_path = os.path.join(self.input_dir, subdir)
            if not os.path.exists(subdir_path):
                continue
            
            pdf_files = [f for f in os.listdir(subdir_path) if f.lower().endswith('.pdf')]
            if not pdf_files:
                continue
            
            print(f"\n📂 Processing {subdir.upper()} folder ({len(pdf_files)} files)...")
            
            if subdir == 'w2':
                # Handle W2 files
                all_w2_data = []
                for pdf_file in pdf_files:
                    pdf_path = os.path.join(subdir_path, pdf_file)
                    print(f"  📄 Reading: {pdf_file}")
                    try:
                        w2_data = self.parse_w2_pdf(pdf_path)
                        all_w2_data.extend(w2_data)
                        print(f"     ✓ Extracted {len(w2_data)} W2 forms")
                    except Exception as e:
                        print(f"     ✗ Error: {str(e)}")
                
                if all_w2_data:
                    output_file = os.path.join(self.output_dir, 'w2.xlsx')
                    df = pd.DataFrame(all_w2_data)
                    
                    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                        df.to_excel(writer, sheet_name='W2_Data', index=False)
                        
                        worksheet = writer.sheets['W2_Data']
                        widths = [30, 30, 15, 15, 15, 15, 15, 15]
                        for i, width in enumerate(widths):
                            if i < len(df.columns):
                                worksheet.column_dimensions[chr(65 + i)].width = width
                        
                        for row in range(2, len(df) + 2):
                            for col in ['C', 'D', 'F', 'G', 'H']:
                                if col <= chr(65 + len(df.columns) - 1):
                                    worksheet[f'{col}{row}'].number_format = '$#,##0.00'
                    
                    print(f"  💾 Saved: {output_file}")
                    total_files += len(pdf_files)
            
            else:
                # Handle regular transaction files
                all_transactions = []
                
                for pdf_file in pdf_files:
                    pdf_path = os.path.join(subdir_path, pdf_file)
                    print(f"  📄 Reading: {pdf_file}")
                    
                    try:
                        if subdir == 'amex' or (subdir == 'other' and 'amex' in pdf_file.lower()):
                            transactions = self.parse_amex_pdf(pdf_path)
                        elif subdir == 'chase' or (subdir == 'other' and 'chase' in pdf_file.lower()):
                            transactions = self.parse_chase_pdf(pdf_path)
                        else:
                            transactions = self.parse_amex_pdf(pdf_path)
                        
                        all_transactions.extend(transactions)
                        print(f"     ✓ Found {len(transactions)} transactions")
                    except Exception as e:
                        print(f"     ✗ Error: {str(e)}")
                
                if all_transactions:
                    output_file = os.path.join(self.output_dir, f'{subdir}.xlsx')
                    df = pd.DataFrame(all_transactions)
                    
                    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                        df.to_excel(writer, sheet_name='Transactions', index=False)
                        
                        worksheet = writer.sheets['Transactions']
                        worksheet.column_dimensions['A'].width = 12
                        worksheet.column_dimensions['B'].width = 50
                        worksheet.column_dimensions['C'].width = 12
                        worksheet.column_dimensions['D'].width = 25
                    
                    print(f"  💾 Saved: {output_file}")
                    total_files += len(pdf_files)
        
        if total_files == 0:
            print("\n❌ No PDF files found in any subdirectory!")
            print("📁 Make sure PDFs are in the correct folders:")
            print("   Convert/amex/   - for AmEx statements")
            print("   Convert/chase/  - for Chase statements")
            print("   Convert/w2/     - for W2 forms")
            print("   Convert/other/  - for other PDFs")
        else:
            print(f"\n✅ Conversion complete! Processed {total_files} files")
            print(f"📁 Check the '{self.output_dir}' folder for results")
            if os.path.exists(report_file):
                print(f"📋 Validation report saved: {report_file}")

def main():
    """Main entry point."""
    converter = SimplePDFConverter()
    converter.convert_all()
    
    print("\n✨ Press Enter to exit...")
    input()

if __name__ == "__main__":
    main()