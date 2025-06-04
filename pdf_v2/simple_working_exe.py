#!/usr/bin/env python3
"""
Simple working version that will work as exe
- Uses simple relative paths
- Includes all parsing logic in one file
- No complex imports or dependencies
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

class SimplePDFConverter:
    def __init__(self):
        # Use simple relative paths
        self.input_dir = 'Convert'
        self.output_dir = 'Excel'
        self.validation_errors = []
        
        # Create directories
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        for subdir in ['amex', 'chase', 'other', 'w2']:
            os.makedirs(os.path.join(self.input_dir, subdir), exist_ok=True)
    
    def parse_amount(self, amount_str):
        """Parse amount string to float."""
        try:
            amount_str = amount_str.replace('$', '').replace(',', '').replace('-', '')
            return float(amount_str)
        except:
            return None
    
    def save_validation_report(self, report_type, errors, total_records):
        """Save validation report."""
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
                f.write("✅ No issues found.\n")
            
            f.write(f"\n{'='*60}\n\n")
    
    def parse_amex_pdf(self, pdf_path):
        """Parse AmEx PDF - Simple version."""
        transactions = []
        current_cardholder = None
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if not text:
                        continue
                    
                    lines = text.split('\n')
                    
                    for line in lines:
                        # Look for cardholder names
                        line_upper = line.strip().upper()
                        if line_upper in VALID_CARDHOLDERS:
                            current_cardholder = line_upper
                            continue
                        
                        # Look for transactions (MM/DD pattern)
                        if re.match(r'^\d{2}/\d{2}', line):
                            if not current_cardholder:
                                # Default to first valid cardholder
                                current_cardholder = 'LUIS RODRIGUEZ'
                            
                            # Extract date, merchant, amount
                            parts = line.split()
                            if len(parts) >= 3:
                                date = parts[0]
                                # Find amount (last number)
                                amount = None
                                for part in reversed(parts):
                                    if re.match(r'[\d,]+\.\d{2}$', part):
                                        amount = self.parse_amount(part)
                                        break
                                
                                if amount and amount > 0:
                                    # Everything between date and amount is merchant
                                    amount_str = str(amount)
                                    if '.' not in amount_str:
                                        amount_str = f"{amount:.2f}"
                                    
                                    # Find merchant by removing date and amount from line
                                    merchant = line
                                    merchant = merchant.replace(date, '', 1).strip()
                                    # Remove amount pattern from end
                                    for part in reversed(parts):
                                        if re.match(r'[\d,]+\.\d{2}$', part):
                                            merchant = merchant.rsplit(part, 1)[0].strip()
                                            break
                                    
                                    transactions.append({
                                        'Name': current_cardholder,
                                        'Date': date + '/24',
                                        'Merchant': merchant,
                                        'Amount': amount
                                    })
        except Exception as e:
            self.save_validation_report('amex', [f"Error: {str(e)}"], 0)
        
        return transactions
    
    def fix_doubled_text(self, text):
        """Fix doubled characters in Chase PDFs."""
        result = []
        i = 0
        while i < len(text):
            if i + 1 < len(text) and text[i] == text[i + 1]:
                result.append(text[i])
                i += 2
            else:
                result.append(text[i])
                i += 1
        return ''.join(result)
    
    def parse_chase_pdf(self, pdf_path):
        """Parse Chase PDF - Simple version with multiple cardholders."""
        transactions = []
        current_cardholder = 'LUIS RODRIGUEZ'  # Default
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if not text:
                        continue
                    
                    # Fix doubled text if needed
                    if 'MMaannaaggee' in text:
                        text = self.fix_doubled_text(text)
                    
                    lines = text.split('\n')
                    
                    for i, line in enumerate(lines):
                        # Check for cardholder sections
                        if 'TRANSACTIONS THIS CYCLE' in line.upper():
                            # Check previous line for name
                            if i > 0:
                                prev_line = lines[i-1].strip().upper()
                                if prev_line in VALID_CARDHOLDERS:
                                    current_cardholder = prev_line
                        
                        # Look for transactions (MM/DD pattern)
                        if re.match(r'^\d{2}/\d{2}', line):
                            # Skip payments
                            if 'Payment Thank You' in line:
                                continue
                            
                            # Find amount at end of line
                            amount_match = re.search(r'([-]?[\d,]+\.\d{2})$', line)
                            if amount_match:
                                amount_str = amount_match.group(1)
                                # Skip negative amounts
                                if amount_str.startswith('-'):
                                    continue
                                
                                amount = self.parse_amount(amount_str)
                                if amount and amount > 0:
                                    # Extract date and merchant
                                    date_match = re.match(r'^(\d{2}/\d{2})', line)
                                    date = date_match.group(1)
                                    
                                    # Merchant is between date and amount
                                    date_end = line.find(date) + len(date)
                                    amount_start = line.rfind(amount_str)
                                    merchant = line[date_end:amount_start].strip()
                                    
                                    # Clean merchant
                                    merchant = merchant.lstrip('& ')
                                    # Remove phone numbers
                                    merchant = re.sub(r'\s+\d{3}-\d{3}-\d{4}.*$', '', merchant)
                                    # Remove state codes at end
                                    merchant = re.sub(r'\s+[A-Z]{2}\s*$', '', merchant)
                                    
                                    transactions.append({
                                        'Name': current_cardholder,
                                        'Date': date + '/24',
                                        'Merchant': merchant,
                                        'Amount': amount
                                    })
        except Exception as e:
            self.save_validation_report('chase', [f"Error: {str(e)}"], 0)
        
        return transactions
    
    def parse_w2_pdf(self, pdf_path):
        """Parse W2 PDF - Simple version."""
        w2_data = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if not text:
                        continue
                    
                    lines = text.split('\n')
                    
                    # Look for SSN pattern to identify W2 forms
                    for i, line in enumerate(lines):
                        if 'social security number' in line.lower():
                            # Initialize W2 record
                            w2_info = {
                                'Employer Name': 'Ocomar Enterprises LLC',  # Default
                                'Employee Name': '',
                                'Gross Salary': 0.0,
                                'Federal Tax': 0.0,
                                'SSN': '',
                                'Medicare': 0.0,
                                'State Witholds': 0.0,
                                'SDI': 0.0
                            }
                            
                            # Get SSN from next line
                            if i + 1 < len(lines):
                                ssn_match = re.search(r'(\d{3}-\d{2}-\d{4})', lines[i + 1])
                                if ssn_match:
                                    w2_info['SSN'] = ssn_match.group(1)
                            
                            # Look for employee name (appears several lines after "Employee's first name")
                            for j in range(max(0, i-20), min(i+20, len(lines))):
                                if "employee's first name" in lines[j].lower():
                                    # Look ahead for the actual name
                                    for k in range(j+1, min(j+8, len(lines))):
                                        potential_name = lines[k].strip()
                                        # Check if it looks like a name
                                        if (len(potential_name) > 5 and 
                                            ' ' in potential_name and
                                            re.match(r'^[A-Z][a-zA-Z]+\s+', potential_name)):
                                            # Clean up the name
                                            potential_name = re.sub(r'\s+[a-z]$', '', potential_name)
                                            potential_name = re.sub(r'\s+\d+.*$', '', potential_name)
                                            w2_info['Employee Name'] = potential_name.strip()
                                            break
                            
                            # Look for wages and federal tax
                            for j in range(max(0, i-10), min(i+10, len(lines))):
                                if 'wages' in lines[j].lower() and 'federal income tax' in lines[j].lower():
                                    # Numbers might be on same line or next line
                                    numbers = re.findall(r'([\d,]+\.?\d{0,2})', lines[j])
                                    if len(numbers) >= 2:
                                        try:
                                            w2_info['Gross Salary'] = float(numbers[0].replace(',', ''))
                                            w2_info['Federal Tax'] = float(numbers[1].replace(',', ''))
                                        except:
                                            pass
                                    elif j + 1 < len(lines):
                                        numbers = re.findall(r'([\d,]+\.?\d{0,2})', lines[j + 1])
                                        if len(numbers) >= 2:
                                            try:
                                                w2_info['Gross Salary'] = float(numbers[0].replace(',', ''))
                                                w2_info['Federal Tax'] = float(numbers[1].replace(',', ''))
                                            except:
                                                pass
                            
                            # Add W2 if we have key data
                            if w2_info['SSN'] and (w2_info['Employee Name'] or w2_info['Gross Salary'] > 0):
                                w2_data.append(w2_info)
        
        except Exception as e:
            self.save_validation_report('w2', [f"Error: {str(e)}"], 0)
        
        return w2_data
    
    def run(self):
        """Run the conversion."""
        print("PDF to Excel Converter")
        print("=" * 50)
        
        # Clear old validation report
        report_file = os.path.join(self.output_dir, 'Validation_Report.txt')
        if os.path.exists(report_file):
            os.remove(report_file)
        
        for subdir in ['amex', 'chase', 'w2']:
            subdir_path = os.path.join(self.input_dir, subdir)
            if not os.path.exists(subdir_path):
                continue
            
            pdf_files = [f for f in os.listdir(subdir_path) if f.lower().endswith('.pdf')]
            if not pdf_files:
                continue
            
            print(f"\nProcessing {subdir.upper()} files...")
            all_data = []
            
            for pdf_file in pdf_files:
                pdf_path = os.path.join(subdir_path, pdf_file)
                print(f"  - {pdf_file}")
                
                try:
                    if subdir == 'amex':
                        data = self.parse_amex_pdf(pdf_path)
                    elif subdir == 'chase':
                        data = self.parse_chase_pdf(pdf_path)
                    elif subdir == 'w2':
                        data = self.parse_w2_pdf(pdf_path)
                    else:
                        continue
                    
                    all_data.extend(data)
                    print(f"    ✓ Extracted {len(data)} records")
                except Exception as e:
                    print(f"    ✗ Error: {str(e)}")
            
            # Always create Excel file
            if subdir == 'w2':
                columns = ['Employer Name', 'Employee Name', 'Gross Salary', 'Federal Tax', 
                          'SSN', 'Medicare', 'State Witholds', 'SDI']
                df = pd.DataFrame(all_data, columns=columns) if all_data else pd.DataFrame(columns=columns)
            else:
                columns = ['Name', 'Date', 'Merchant', 'Amount']
                df = pd.DataFrame(all_data, columns=columns) if all_data else pd.DataFrame(columns=columns)
            
            output_file = os.path.join(self.output_dir, f'{subdir}.xlsx')
            
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Data', index=False)
                
                # Format columns
                worksheet = writer.sheets['Data']
                for i in range(len(df.columns)):
                    worksheet.column_dimensions[chr(65 + i)].width = 20
            
            print(f"\n✅ Saved {len(all_data)} records to: {output_file}")
            self.save_validation_report(subdir, [], len(all_data))
        
        print("\nConversion complete!")
        print("\nPress Enter to exit...")
        input()

if __name__ == "__main__":
    converter = SimplePDFConverter()
    converter.run()