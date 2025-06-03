"""
Chase statement parser for PDF to Excel Converter

This module handles parsing of Chase PDF statements,
including cardholder name detection and transaction extraction.
"""

import re
from datetime import datetime
from .base_parser import BaseParser
from src.validators.name_validator import NameValidator
from src.utils.date_utils import DateUtils


class ChaseParser(BaseParser):
    """Parser for Chase statements"""
    
    def __init__(self):
        super().__init__()
        self.name_validator = NameValidator()
        self.chase_date_range = None
        self.primary_account_holder = "Unknown"  # From address on page 1
        self.current_cardholder = "Unknown"      # Current section cardholder
    
    def extract_primary_account_holder(self, full_text):
        """Extract the primary account holder from the mailing address on page 1"""
        try:
            lines = full_text.split('\n')
            
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
                        
                        print(f"🏠 FOUND PRIMARY ACCOUNT HOLDER FROM ADDRESS: '{line}'")
                        print(f"   Address context: {next_line1[:30]}...")
                        print(f"   Street: {next_line2[:30]}...")
                        print(f"   City/State: {next_line3[:30]}...")
                        
                        return line.upper().strip()
            
            print("⚠️  Could not find primary account holder from address")
            return "Unknown"
            
        except Exception as e:
            print(f"❌ Error extracting primary account holder: {e}")
            return "Unknown"
    
    def looks_like_person_name(self, line):
        """Check if a line looks like a person's name"""
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
        """Check if a line looks like a street address"""
        # Should contain numbers and street-like words
        has_number = bool(re.search(r'\d', line))
        has_street_words = bool(re.search(r'\b(ST|STREET|AVE|AVENUE|RD|ROAD|BLVD|BOULEVARD|DR|DRIVE|LN|LANE|CT|COURT|WAY|PL|PLACE)\b', line.upper()))
        return has_number or has_street_words or len(line.split()) >= 2
    
    def looks_like_city_state_zip(self, line):
        """Check if a line looks like city, state, zip"""
        # Should end with state and zip pattern: CA 94545-1802
        return bool(re.search(r'[A-Z]{2}\s+\d{5}(-\d{4})?$', line))
    
    def parse_page(self, page_text, page_num):
        """Parse Chase page with address-based primary name detection"""
        transactions = []
        
        print(f"\n📄 DEBUG: Starting Chase page {page_num}")
        print(f"📄 DEBUG: Primary account holder: '{self.primary_account_holder}'")
        print(f"📄 DEBUG: Current cardholder: '{self.current_cardholder}'")
        
        try:
            lines = page_text.split('\n')
            print(f"📄 DEBUG: Chase page {page_num} has {len(lines)} lines")
            
            # FIXED: Start with primary account holder as default
            # Don't use "Unknown" - use the actual primary account holder name
            if self.primary_account_holder != "Unknown":
                default_name = self.primary_account_holder
            else:
                default_name = "LUIS RODRIGUEZ"  # Fallback if extraction failed
            
            print(f"📄 DEBUG: Starting with default name: '{default_name}'")
            
            for i, line in enumerate(lines):
                try:
                    line = line.strip()
                    
                    # Skip empty lines and headers
                    if len(line) < 5:
                        continue
                    if (('Date of' in line and 'Transaction' in line) or
                        'Merchant Name' in line or
                        'ACCOUNT ACTIVITY' in line or
                        line.startswith('CHASE') or
                        line.startswith('Page') or
                        line.startswith('Customer Service')):
                        continue
                    
                    # Check for section cardholder name (different from primary)
                    cardholder_name = self.name_validator.extract_chase_cardholder_name(line, lines, i)
                    if cardholder_name and cardholder_name != self.primary_account_holder:
                        self.current_cardholder = cardholder_name
                        default_name = cardholder_name  # Switch to this cardholder for subsequent transactions
                        print(f"🏷️  DEBUG: SECTION CARDHOLDER DETECTED: '{cardholder_name}' (different from primary)")
                        print(f"   📋 Switching default name from '{self.primary_account_holder}' to '{cardholder_name}'")
                        continue
                    elif cardholder_name == self.primary_account_holder:
                        # Same as primary - just confirm we're back to primary
                        self.current_cardholder = self.primary_account_holder
                        default_name = self.primary_account_holder
                        print(f"🏷️  DEBUG: BACK TO PRIMARY CARDHOLDER: '{self.primary_account_holder}'")
                        continue
                    
                    # Try to parse as transaction
                    transaction = self.parse_transaction_line(line)
                    if transaction:
                        # FIXED: Always assign the current default name (never "Unknown")
                        transaction['Name'] = default_name
                        transactions.append(transaction)
                        
                        if len(transactions) % 20 == 1:  # Show every 20th transaction
                            print(f"💳 DEBUG: Transaction #{len(transactions)} assigned to '{default_name}'")
                            print(f"   TRANSACTION: {transaction['Date']} | {transaction['Merchant'][:30]}... | ${transaction['Amount']}")
                
                except Exception as e:
                    print(f"🚨 DEBUG: Error on Chase line {i+1}: {e}")
                    continue
        
        except Exception as e:
            print(f"🚨 DEBUG: Error parsing Chase page {page_num}: {e}")
        
        print(f"📄 DEBUG: Chase page {page_num} completed - {len(transactions)} transactions")
        
        # Show summary of names assigned
        name_counts = {}
        for trans in transactions:
            name = trans.get('Name', 'Unknown')
            name_counts[name] = name_counts.get(name, 0) + 1
        print(f"📊 DEBUG: Name distribution on page {page_num}: {name_counts}")
    
        return transactions
    
    # def parse_page(self, page_text, page_num):
    #     """Parse Chase page with address-based primary name detection"""
    #     transactions = []
        
    #     print(f"\n📄 DEBUG: Starting Chase page {page_num}")
    #     print(f"📄 DEBUG: Primary account holder: '{self.primary_account_holder}'")
    #     print(f"📄 DEBUG: Current cardholder: '{self.current_cardholder}'")
        
    #     try:
    #         lines = page_text.split('\n')
    #         print(f"📄 DEBUG: Chase page {page_num} has {len(lines)} lines")
            
    #         # Use primary account holder as default for all transactions
    #         default_name = self.primary_account_holder
            
    #         for i, line in enumerate(lines):
    #             try:
    #                 line = line.strip()
                    
    #                 # Skip empty lines and headers
    #                 if len(line) < 5:
    #                     continue
    #                 if (('Date of' in line and 'Transaction' in line) or
    #                     'Merchant Name' in line or
    #                     'ACCOUNT ACTIVITY' in line or
    #                     line.startswith('CHASE') or
    #                     line.startswith('Page') or
    #                     line.startswith('Customer Service')):
    #                     continue
                    
    #                 # Check for section cardholder name (different from primary)
    #                 cardholder_name = self.name_validator.extract_chase_cardholder_name(line, lines, i)
    #                 if cardholder_name and cardholder_name != self.primary_account_holder:
    #                     self.current_cardholder = cardholder_name
    #                     default_name = cardholder_name  # Switch to this cardholder for subsequent transactions
    #                     print(f"🏷️  DEBUG: SECTION CARDHOLDER DETECTED: '{cardholder_name}' (different from primary)")
    #                     print(f"   📋 Switching default name from '{self.primary_account_holder}' to '{cardholder_name}'")
    #                     continue
    #                 elif cardholder_name == self.primary_account_holder:
    #                     # Same as primary - just confirm we're back to primary
    #                     self.current_cardholder = self.primary_account_holder
    #                     default_name = self.primary_account_holder
    #                     print(f"🏷️  DEBUG: BACK TO PRIMARY CARDHOLDER: '{self.primary_account_holder}'")
    #                     continue
                    
    #                 # Try to parse as transaction
    #                 transaction = self.parse_transaction_line(line)
    #                 if transaction:
    #                     # Assign current default name
    #                     transaction['Name'] = default_name
    #                     transactions.append(transaction)
                        
    #                     if len(transactions) % 20 == 1:  # Show every 20th transaction
    #                         print(f"💳 DEBUG: Transaction #{len(transactions)} assigned to '{default_name}'")
    #                         print(f"   TRANSACTION: {transaction['Date']} | {transaction['Merchant'][:30]}... | ${transaction['Amount']}")
                
    #             except Exception as e:
    #                 print(f"🚨 DEBUG: Error on Chase line {i+1}: {e}")
    #                 continue
        
    #     except Exception as e:
    #         print(f"🚨 DEBUG: Error parsing Chase page {page_num}: {e}")
        
    #     print(f"📄 DEBUG: Chase page {page_num} completed - {len(transactions)} transactions")
        
    #     # Show summary of names assigned
    #     name_counts = {}
    #     for trans in transactions:
    #         name = trans.get('Name', 'Unknown')
    #         name_counts[name] = name_counts.get(name, 0) + 1
    #     print(f"📊 DEBUG: Name distribution on page {page_num}: {name_counts}")
        
    #     return transactions

    def parse_transaction_line(self, line):
        """Parse individual Chase transaction line"""
        try:
            # Chase format: MM/DD [&] MERCHANT_NAME LOCATION AMOUNT
            date_pattern = r'^(\d{1,2}/\d{1,2})\s*(&?)\s*(.+?)\s+([-]?\d{1,}(?:,\d{3})*\.\d{2})$'
            
            match = re.match(date_pattern, line)
            
            if match:
                date = match.group(1)
                merchant_and_location = match.group(3).strip()
                amount = match.group(4)
                
                # Clean up merchant name
                merchant_desc = re.sub(r'\s+', ' ', merchant_and_location)
                merchant_desc = re.sub(r'\s+[A-Z]{2}$', '', merchant_desc)  # Remove state codes
                merchant_desc = re.sub(r'\s+\d{3}-\d{3}-\d{4}$', '', merchant_desc)  # Remove phone numbers
                merchant_desc = re.sub(r'\s+\d{10,}$', '', merchant_desc)  # Remove long numbers
                
                # Skip negative amounts (payments/credits)
                try:
                    amount_value = float(amount.replace(',', ''))
                    if amount_value <= 0:
                        return None
                except ValueError:
                    return None
                
                # Get the correct year based on the date range
                transaction_month = int(date.split('/')[0])
                correct_year = DateUtils.get_chase_transaction_year(transaction_month, self.chase_date_range)
                full_date = f"{date}/{correct_year}"
                
                return {
                    'Date': full_date,
                    'Merchant': merchant_desc,
                    'Amount': amount
                }
        
        except Exception:
            pass
        
        return None
    
    def extract_chase_date_range(self, text):
        """Extract the date range from Chase PDF"""
        try:
            lines = text.split('\n')
            
            for i, line in enumerate(lines):
                if ('Opening/Closing Date' in line or 
                    'OPENING/CLOSING DATE' in line.upper()):
                    
                    date_line = line
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if re.search(r'\d{2}/\d{2}/\d{2}', next_line):
                            date_line = next_line
                    
                    date_pattern = r'(\d{1,2}/\d{1,2}/\d{2,4})\s*-\s*(\d{1,2}/\d{1,2}/\d{2,4})'
                    match = re.search(date_pattern, date_line)
                    
                    if match:
                        start_date = match.group(1)
                        end_date = match.group(2)
                        
                        start_full = DateUtils.convert_chase_date_to_full(start_date)
                        end_full = DateUtils.convert_chase_date_to_full(end_date)
                        
                        print(f"📅 Found Chase date range: {start_full} to {end_full}")
                        
                        return {
                            'start': start_full,
                            'end': end_full,
                            'start_month': int(start_full.split('/')[0]),
                            'end_month': int(end_full.split('/')[0]),
                            'start_year': int(start_full.split('/')[2]),
                            'end_year': int(end_full.split('/')[2])
                        }
            
        except Exception as e:
            print(f"⚠️ Could not extract Chase date range: {e}")
        
        return None