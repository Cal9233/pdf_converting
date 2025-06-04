#!/usr/bin/env python3
"""
Updated PDF to Excel Converter - Always creates Excel files
Even if 0 transactions found, still creates the Excel file
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
        self.input_dir = 'Convert'
        self.output_dir = 'Excel'
        self.validation_errors = []
        
        # Create directories
        for dir_path in [self.input_dir, self.output_dir]:
            os.makedirs(dir_path, exist_ok=True)
        
        for subdir in ['amex', 'chase', 'other', 'w2']:
            os.makedirs(os.path.join(self.input_dir, subdir), exist_ok=True)
    
    def is_business_name(self, name):
        """Check if name contains business indicators."""
        upper_name = name.upper()
        return any(indicator in upper_name for indicator in BUSINESS_INDICATORS)
    
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
    
    def parse_amount(self, amount_str):
        """Parse amount string to float."""
        try:
            # Remove $ and commas
            amount_str = amount_str.replace('$', '').replace(',', '')
            return float(amount_str)
        except:
            return None
    
    def clean_merchant(self, merchant):
        """Clean merchant name."""
        # Remove extra spaces
        merchant = ' '.join(merchant.split())
        # Remove trailing reference numbers
        merchant = re.sub(r'\s+\d{3}-\d{3}-\d{4}$', '', merchant)
        merchant = re.sub(r'\s+#\d+$', '', merchant)
        return merchant.strip()
    
    def parse_amex_pdf(self, pdf_path):
        """Parse AmEx PDF."""
        transactions = []
        validation_errors = []
        current_cardholder = None
        found_cardholders = set()
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    validation_errors.append(f"Page {page_num + 1}: No text extracted")
                    continue
                
                lines = text.split('\n')
                page_transactions = 0
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Check for cardholder name
                    if line.isupper() and len(line.split()) <= 3:
                        name = self.extract_cardholder_name(line)
                        if name and not self.is_business_name(line):
                            current_cardholder = name
                            found_cardholders.add(name)
                            continue
                    
                    # Parse transaction (MM/DD or MM/DD/YY pattern)
                    match = re.match(r'^(\d{2}/\d{2}(?:/\d{2})?)\s+(.+?)\s+(\$?[\d,]+\.\d{2})$', line)
                    if match:
                        if not current_cardholder:
                            validation_errors.append(f"Transaction found without cardholder on page {page_num + 1}: {line[:50]}...")
                            continue
                            
                        date_str = match.group(1)
                        merchant = match.group(2)
                        amount = self.parse_amount(match.group(3))
                        
                        if amount:
                            # Parse date
                            if len(date_str) == 5:  # MM/DD
                                date_str += '/24'  # Add year
                            try:
                                date = datetime.strptime(date_str, '%m/%d/%y').strftime('%m/%d/%Y')
                                transactions.append({
                                    'Name': current_cardholder,
                                    'Date': date,
                                    'Merchant': self.clean_merchant(merchant),
                                    'Amount': amount
                                })
                                page_transactions += 1
                            except Exception as e:
                                validation_errors.append(f"Date parsing error on page {page_num + 1}: {date_str} - {str(e)}")
                        else:
                            validation_errors.append(f"Amount parsing error on page {page_num + 1}: {match.group(3)}")
                
                # Check if page had potential transactions but none were extracted
                if page_transactions == 0 and any(re.match(r'^\d{2}/\d{2}', line) for line in lines):
                    validation_errors.append(f"Page {page_num + 1}: Found date patterns but no transactions extracted")
        
        # Save validation report
        self.save_validation_report('amex', validation_errors, len(transactions))
        
        return transactions
    
    def parse_chase_pdf(self, pdf_path):
        """Parse Chase PDF."""
        transactions = []
        validation_errors = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if not text:
                        validation_errors.append(f"Page {page_num + 1}: No text extracted")
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
                                        'Name': cardholder,
                                        'Date': date + '/24',  # Add year
                                        'Merchant': description,
                                        'Amount': self.parse_amount(amount)
                                    })
                                else:
                                    validation_errors.append(f"Page {page_num + 1}: Transaction without cardholder - {line[:50]}...")
        except Exception as e:
            validation_errors.append(f"Error parsing Chase PDF: {str(e)}")
        
        # Save validation report
        self.save_validation_report('chase', validation_errors, len(transactions))
        
        return transactions
    
    def parse_w2_pdf(self, pdf_path):
        """Parse W2 PDF for tax information."""
        w2_data = []
        validation_errors = []
        
        with pdfplumber.open(pdf_path) as pdf:
            # First, find all SSNs to identify W2 forms
            all_ssns = []
            ssn_pattern = r'(\d{3}-\d{2}-\d{4})'
            
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                
                # Find all SSN positions on this page
                for i, line in enumerate(lines):
                    if 'social security number' in line.lower() and i + 1 < len(lines):
                        # Check next line for SSN
                        ssn_match = re.search(ssn_pattern, lines[i + 1])
                        if ssn_match:
                            all_ssns.append((page_num, i, ssn_match.group(1)))
            
            print(f"    Found {len(all_ssns)} W2 forms by SSN detection")
            
            # Now process each SSN/W2 form found
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                
                # Find SSN positions on this page
                ssn_positions = []
                for i, line in enumerate(lines):
                    if 'social security number' in line.lower() and i + 1 < len(lines):
                        ssn_match = re.search(ssn_pattern, lines[i + 1])
                        if ssn_match:
                            ssn_positions.append((i, ssn_match.group(1)))
                
                # Process each W2 form found on this page
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
                                # Look for amount in next line
                                amount_match = re.search(r'([\d,]+\.?\d{0,2})', form_lines[i + 1])
                                if amount_match:
                                    try:
                                        w2_info['Federal Tax'] = float(amount_match.group(1).replace(',', ''))
                                    except:
                                        pass
                        
                        # Wages (Box 1) - adjusted pattern
                        if 'wages' in line.lower() and 'tips' in line.lower() and 'social security wages' not in line.lower():
                            if i + 1 < len(form_lines):
                                # Look for amount in next line
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
                                        # Second number is state tax withheld
                                        w2_info['State Witholds'] = float(numbers[1].replace(',', ''))
                                    except:
                                        pass
                        
                        # Employer name (Box c)
                        if "employer's name" in line.lower():
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
                    
                    # Validate and add to list
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
                    
                    # Add to results even if some fields are missing
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
    
    def run(self):
        """Run the conversion process."""
        print("PDF to Excel Converter")
        print("=" * 50)
        
        # Clear old validation report
        report_file = os.path.join(self.output_dir, 'Validation_Report.txt')
        if os.path.exists(report_file):
            os.remove(report_file)
        
        subdirs = ['amex', 'chase', 'other', 'w2']
        
        for subdir in subdirs:
            subdir_path = os.path.join(self.input_dir, subdir)
            if not os.path.exists(subdir_path):
                continue
                
            pdf_files = [f for f in os.listdir(subdir_path) if f.lower().endswith('.pdf')]
            
            if not pdf_files:
                continue
            
            print(f"\nProcessing {subdir.upper()} files...")
            
            if subdir == 'w2':
                # Handle W2 files differently
                all_w2_data = []
                
                for pdf_file in pdf_files:
                    pdf_path = os.path.join(subdir_path, pdf_file)
                    print(f"  - {pdf_file}")
                    
                    try:
                        w2_data = self.parse_w2_pdf(pdf_path)
                        all_w2_data.extend(w2_data)
                        print(f"    ✓ Extracted {len(w2_data)} W-2 forms")
                    except Exception as e:
                        print(f"    ✗ Error: {str(e)}")
                        self.save_validation_report('w2', [f"Error processing {pdf_file}: {str(e)}"], 0)
                
                # ALWAYS create W2 Excel file, even if empty
                df = pd.DataFrame(all_w2_data) if all_w2_data else pd.DataFrame(columns=[
                    'Employer Name', 'Employee Name', 'Gross Salary', 'Federal Tax', 
                    'SSN', 'Medicare', 'State Witholds', 'SDI'
                ])
                
                # Use fixed filename without timestamp
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
                
                print(f"\n✅ Saved {len(all_w2_data)} W-2 forms to: {output_file}")
            
            else:
                # Handle regular transaction files
                all_transactions = []
                
                for pdf_file in pdf_files:
                    pdf_path = os.path.join(subdir_path, pdf_file)
                    print(f"  - {pdf_file}")
                    
                    try:
                        if subdir == 'amex' or (subdir == 'other' and 'amex' in pdf_file.lower()):
                            transactions = self.parse_amex_pdf(pdf_path)
                        elif subdir == 'chase' or (subdir == 'other' and 'chase' in pdf_file.lower()):
                            transactions = self.parse_chase_pdf(pdf_path)
                        else:
                            # Default to AmEx parser
                            transactions = self.parse_amex_pdf(pdf_path)
                        
                        all_transactions.extend(transactions)
                        print(f"    ✓ Extracted {len(transactions)} transactions")
                    except Exception as e:
                        print(f"    ✗ Error: {str(e)}")
                        self.save_validation_report(subdir, [f"Error processing {pdf_file}: {str(e)}"], 0)
                
                # ALWAYS create Excel file, even if empty
                if all_transactions:
                    df = pd.DataFrame(all_transactions)
                    df = df[['Name', 'Date', 'Merchant', 'Amount']]
                    df = df.sort_values(['Name', 'Date'])
                else:
                    # Create empty dataframe with correct columns
                    df = pd.DataFrame(columns=['Name', 'Date', 'Merchant', 'Amount'])
                    # Add note to validation report
                    self.save_validation_report(subdir, [f"No transactions found in {len(pdf_files)} PDF file(s)"], 0)
                
                # Use fixed filename without timestamp
                output_file = os.path.join(self.output_dir, f'{subdir}.xlsx')
                
                with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Transactions', index=False)
                    
                    worksheet = writer.sheets['Transactions']
                    for col in ['A', 'B', 'C', 'D']:
                        worksheet.column_dimensions[col].width = [25, 12, 50, 12][ord(col) - 65]
                    
                    # Format amount column
                    for row in range(2, len(df) + 2):
                        worksheet[f'D{row}'].number_format = '$#,##0.00'
                
                print(f"\n✅ Saved {len(df)} transactions to: {output_file}")
        
        print("\nConversion complete!")
        
        # Check if validation report exists and has content
        if os.path.exists(report_file):
            print(f"\n⚠️  Validation Report created at: {report_file}")
            print("Please review for any potential issues or missing data.")

if __name__ == "__main__":
    converter = SimplePDFConverter()
    converter.run()