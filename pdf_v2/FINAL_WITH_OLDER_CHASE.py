#!/usr/bin/env python3
"""
Standalone PDF to Excel Converter - With Older_program Chase parsing logic
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
        # For exe, use the directory where the exe is located
        if getattr(sys, 'frozen', False):
            # Running as compiled exe
            self.base_dir = os.path.dirname(sys.executable)
        else:
            # Running as script
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
            
        self.input_dir = os.path.join(self.base_dir, 'Convert')
        self.output_dir = os.path.join(self.base_dir, 'Excel')
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
        for valid_name in VALID_CARDHOLDERS:
            if valid_name in text:
                return valid_name
        return None
    
    def is_business_name(self, text):
        """Check if text contains business indicators."""
        text_upper = text.upper()
        for indicator in BUSINESS_INDICATORS:
            if indicator in text_upper:
                return True
        return False
    
    def parse_amount(self, text):
        """Extract amount from text."""
        matches = re.findall(r'\$?[\d,]+\.?\d{0,2}', text)
        for match in reversed(matches):
            amount_str = match.replace('$', '').replace(',', '')
            try:
                return float(amount_str)
            except ValueError:
                continue
        return None
    
    def clean_merchant(self, merchant):
        """Clean merchant name - matching Older_program's chase_parser.py exactly."""
        # Clean up merchant name
        merchant_desc = re.sub(r'\s+', ' ', merchant)  # Consolidate spaces
        merchant_desc = re.sub(r'\s+[A-Z]{2}$', '', merchant_desc)  # Remove state codes
        merchant_desc = re.sub(r'\s+\d{3}-\d{3}-\d{4}$', '', merchant_desc)  # Remove phone numbers
        merchant_desc = re.sub(r'\s+\d{10,}$', '', merchant_desc)  # Remove long numbers
        
        return merchant_desc
    
    def fix_doubled_text(self, text):
        """Fix doubled characters in text (e.g., 'MMaannaaggee' -> 'Manage')."""
        if not text:
            return text
            
        # Check if text appears to have doubled characters
        doubled_count = 0
        for i in range(0, len(text) - 1, 2):
            if i + 1 < len(text) and text[i] == text[i + 1]:
                doubled_count += 1
        
        # If more than 30% of character pairs are doubled, fix it
        if doubled_count > len(text) / 4:
            fixed_text = ''
            i = 0
            while i < len(text):
                if i + 1 < len(text) and text[i] == text[i + 1]:
                    fixed_text += text[i]
                    i += 2
                else:
                    fixed_text += text[i]
                    i += 1
            return fixed_text
        
        return text
    
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
    
    def extract_primary_account_holder(self, text):
        """Extract the primary account holder from the mailing address on page 1."""
        try:
            lines = text.split('\n')
            
            # Look for address pattern: NAME followed by address lines
            for i, line in enumerate(lines[:50]):  # Check first 50 lines (page 1)
                line = line.strip()
                
                # Skip empty lines and obvious non-names
                if len(line) < 5 or any(skip in line.upper() for skip in ['CHASE', 'ACCOUNT', 'STATEMENT', 'PAGE', 'DATE']):
                    continue
                
                # Look for a potential name followed by address components
                if i + 3 < len(lines):  # Make sure we have enough lines ahead
                    next_line1 = lines[i + 1].strip()
                    next_line2 = lines[i + 2].strip()
                    next_line3 = lines[i + 3].strip()
                    
                    # Check if this looks like: NAME, COMPANY/ADDRESS, STREET, CITY STATE ZIP
                    if (self.looks_like_person_name(line) and 
                        self.looks_like_address_component(next_line2) and
                        self.looks_like_city_state_zip(next_line3)):
                        
                        # Check if it's a valid cardholder
                        name_upper = line.upper().strip()
                        if name_upper in VALID_CARDHOLDERS:
                            return name_upper
            
            return None
            
        except Exception as e:
            return None
    
    def looks_like_person_name(self, line):
        """Check if a line looks like a person's name."""
        # Must be 2-4 words, mostly letters, not too long
        words = line.split()
        if len(words) < 2 or len(words) > 4:
            return False
        
        # Check each word is mostly letters
        for word in words:
            if len(word) < 2 or not re.match(r'^[A-Za-z\-\'\.]+$', word):
                return False
        
        # Avoid obvious business terms
        business_terms = ['LLC', 'INC', 'CORP', 'ENTERPRISES', 'COMPANY', 'BUSINESS']
        if any(term in line.upper() for term in business_terms):
            return False
            
        return True
    
    def looks_like_address_component(self, line):
        """Check if a line looks like a street address."""
        # Should contain numbers and street-like words
        has_number = bool(re.search(r'\d', line))
        has_street_words = bool(re.search(r'\b(ST|STREET|AVE|AVENUE|RD|ROAD|BLVD|BOULEVARD|DR|DRIVE|LN|LANE|CT|COURT|WAY|PL|PLACE)\b', line.upper()))
        return has_number or has_street_words or len(line.split()) >= 2
    
    def looks_like_city_state_zip(self, line):
        """Check if a line looks like city, state, zip."""
        # Should end with state and zip pattern: CA 94545-1802
        return bool(re.search(r'[A-Z]{2}\s+\d{5}(-\d{4})?$', line))
    
    def parse_chase_pdf(self, pdf_path):
        """Parse Chase PDF using Older_program logic with multiple cardholder support."""
        transactions = []
        validation_errors = []
        primary_cardholder = None
        current_cardholder = None
        
        with pdfplumber.open(pdf_path) as pdf:
            # First, extract primary cardholder from first page address
            if pdf.pages:
                text = pdf.pages[0].extract_text()
                if text:
                    # Fix doubled text if needed
                    text = self.fix_doubled_text(text)
                    primary_cardholder = self.extract_primary_account_holder(text)
            
            # Use fallback if extraction failed
            if not primary_cardholder:
                primary_cardholder = 'LUIS RODRIGUEZ'
            
            current_cardholder = primary_cardholder
            
            # Process all pages
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    validation_errors.append(f"Page {page_num + 1}: No text extracted")
                    continue
                
                # Fix doubled text if needed
                text = self.fix_doubled_text(text)
                lines = text.split('\n')
                page_transactions = 0
                
                # Start each page with primary cardholder as default
                default_name = primary_cardholder
                
                for i, line in enumerate(lines):
                    line_stripped = line.strip()
                    
                    # Skip headers and empty lines
                    if len(line_stripped) < 5:
                        continue
                    if (('Date of' in line_stripped and 'Transaction' in line_stripped) or
                        'Merchant Name' in line_stripped or
                        'ACCOUNT ACTIVITY' in line_stripped or
                        line_stripped.startswith('CHASE') or
                        line_stripped.startswith('Page') or
                        line_stripped.startswith('Customer Service')):
                        continue
                    
                    # Pattern 1: Look for "TRANSACTIONS THIS CYCLE (CARD XXXX)" pattern
                    if 'TRANSACTIONS THIS CYCLE' in line.upper() and 'CARD' in line.upper():
                        # The name should be on the previous line(s)
                        if i > 0:
                            prev_line = lines[i - 1].strip()
                            if prev_line.upper() in VALID_CARDHOLDERS:
                                current_cardholder = prev_line.upper()
                                default_name = current_cardholder
                                continue
                    
                    # Pattern 2: Name and TRANSACTIONS THIS CYCLE on same line
                    if 'TRANSACTIONS THIS CYCLE' in line.upper():
                        parts = line.split('TRANSACTIONS THIS CYCLE')
                        if parts:
                            potential_name = parts[0].strip().upper()
                            if potential_name in VALID_CARDHOLDERS:
                                current_cardholder = potential_name
                                default_name = current_cardholder
                                continue
                    
                    # Pattern 3: Standalone cardholder names (2-4 words, all caps)
                    if (len(line_stripped.split()) >= 2 and len(line_stripped.split()) <= 4 and 
                        line_stripped.isupper() and not any(char.isdigit() for char in line_stripped)):
                        potential_name = line_stripped.upper()
                        if potential_name in VALID_CARDHOLDERS:
                            # Verify by checking next few lines for TRANSACTIONS THIS CYCLE
                            for j in range(i+1, min(i+8, len(lines))):
                                if 'TRANSACTIONS THIS CYCLE' in lines[j].upper():
                                    current_cardholder = potential_name
                                    default_name = current_cardholder
                                    break
                    
                    # Parse transaction with Chase format: MM/DD [&] MERCHANT_NAME LOCATION AMOUNT
                    date_pattern = r'^(\d{1,2}/\d{1,2})\s*(&?)\s*(.+?)\s+([-]?\d{1,}(?:,\d{3})*\.\d{2})$'
                    match = re.match(date_pattern, line_stripped)
                    
                    if match:
                        date_str = match.group(1)
                        # Skip the & in group(2)
                        merchant = match.group(3).strip()
                        amount_str = match.group(4)
                        
                        # Skip negative amounts (payments/credits)
                        if amount_str.startswith('-'):
                            continue
                        
                        # Skip payment lines
                        if 'Payment Thank You' in merchant:
                            continue
                        
                        # Parse amount
                        try:
                            amount = float(amount_str.replace(',', ''))
                            if amount <= 0:
                                continue
                        except ValueError:
                            continue
                        
                        # Format date
                        try:
                            # Normalize date format
                            month, day = date_str.split('/')
                            date_str_normalized = f"{int(month):02d}/{int(day):02d}/24"
                            date = datetime.strptime(date_str_normalized, '%m/%d/%y').strftime('%m/%d/%Y')
                            
                            transactions.append({
                                'Name': default_name,
                                'Date': date,
                                'Merchant': self.clean_merchant(merchant),
                                'Amount': amount
                            })
                            page_transactions += 1
                        except Exception as e:
                            validation_errors.append(f"Date parsing error on page {page_num + 1}: {date_str} - {str(e)}")
                
                # Check if page had potential transactions but none were extracted
                if page_transactions == 0 and any(re.match(r'^\d{1,2}/\d{1,2}', line) for line in lines):
                    validation_errors.append(f"Page {page_num + 1}: Found date patterns but no transactions extracted")
        
        # Save validation report
        self.save_validation_report('chase', validation_errors, len(transactions))
        
        return transactions
    
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
            
            print(f"    Found {len(ssn_positions)} W2 forms by SSN detection")
            
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
                
                # Default employer name if not found
                if not w2_info['Employer Name']:
                    w2_info['Employer Name'] = 'Ocomar Enterprises LLC'
                
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
    
    def extract_amount_from_line(self, line):
        """Extract dollar amount from a line of text."""
        # Look for patterns like $1,234.56 or 1234.56
        matches = re.findall(r'\$?([\d,]+\.?\d{0,2})', line)
        for match in matches:
            try:
                return float(match.replace(',', ''))
            except:
                continue
        return 0.0
    
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
        """Run the conversion."""
        print("\nPDF to Excel Converter")
        print("=" * 50)
        
        # Clear validation report at start
        report_file = os.path.join(self.output_dir, 'Validation_Report.txt')
        if os.path.exists(report_file):
            os.remove(report_file)
        
        has_validation_errors = False
        
        for subdir in ['amex', 'chase', 'other', 'w2']:
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
                
                if all_w2_data:
                    # Save W2 data with custom format
                    df = pd.DataFrame(all_w2_data)
                    df = df[['Employer Name', 'Employee Name', 'Gross Salary', 'Federal Tax', 
                            'SSN', 'Medicare', 'State Witholds', 'SDI']]
                    
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
                    
                    print(f"\n✅ Saved {len(df)} W-2 forms to: {output_file}")
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
                            transactions = self.parse_amex_pdf(pdf_path)  # Default
                        
                        all_transactions.extend(transactions)
                        print(f"    ✓ Extracted {len(transactions)} transactions")
                    except Exception as e:
                        print(f"    ✗ Error: {str(e)}")
                
                if all_transactions:
                    # Save to Excel
                    df = pd.DataFrame(all_transactions)
                    df = df[['Name', 'Date', 'Merchant', 'Amount']]
                    # Don't sort - preserve original PDF order like Older_program does
                    
                    # Use fixed filename without timestamp
                    output_file = os.path.join(self.output_dir, f'{subdir}.xlsx')
                    
                    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                        df.to_excel(writer, sheet_name='Transactions', index=False)
                        
                        worksheet = writer.sheets['Transactions']
                        for col in ['A', 'B', 'C', 'D']:
                            worksheet.column_dimensions[col].width = [25, 12, 50, 12][ord(col) - 65]
                        
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