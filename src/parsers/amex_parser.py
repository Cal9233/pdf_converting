import re
from datetime import datetime
from .base_parser import BaseParser
from src.validators.name_validator import NameValidator
from src.utils.date_utils import DateUtils

class AmexParser(BaseParser):
    """Parser for American Express statements"""
    
    def __init__(self):
        super().__init__()
        self.name_validator = NameValidator()
        self.global_current_cardholder = "Unknown"    

    def parse_amex_page_global(self, page_text, page_num):
        """Parse AmEx page using global cardholder tracking"""
        transactions = []
        
        print(f"\n📄 DEBUG: Starting page {page_num} with global cardholder: '{self.global_current_cardholder}'")
        
        try:
            lines = page_text.split('\n')
            print(f"📄 DEBUG: Page {page_num} has {len(lines)} lines")
            
            for i, line in enumerate(lines):
                try:
                    line = line.strip()
                    
                    # Skip empty lines
                    if len(line) < 5:
                        continue
                    
                    # Skip obvious headers
                    if (('Merchant Name' in line and '$ Amount' in line) or
                        'Date of Transaction' in line or
                        line.startswith('Amazon Business Prime Card') or
                        line.startswith('AMERICAN EXPRESS') or
                        line.startswith('Page ') or
                        line.startswith('Customer Care')):
                        continue
                    
                    # Check for continuation headers - preserve current name
                    if self.is_continuation_header(line):
                        print(f"📋 DEBUG: Continuation header on line {i+1}: '{line}'")
                        print(f"   🔄 PRESERVING global cardholder: '{self.global_current_cardholder}'")
                        continue
                    
                    # Check for new cardholder name
                    cardholder_name = self.extract_cardholder_name(line)
                    if cardholder_name:
                        old_cardholder = self.global_current_cardholder
                        self.global_current_cardholder = cardholder_name
                        print(f"🏷️  DEBUG: GLOBAL CARDHOLDER CHANGED on line {i+1}")
                        print(f"   FROM: '{old_cardholder}' TO: '{self.global_current_cardholder}'")
                        continue
                    
                    # Parse transaction
                    transaction = self.parse_amex_transaction_line(line)
                    if transaction:
                        # Use GLOBAL cardholder
                        transaction['Name'] = self.global_current_cardholder
                        transactions.append(transaction)
                        print(f"💳 DEBUG: Transaction on line {i+1}")
                        print(f"   ASSIGNED TO: '{self.global_current_cardholder}'")
                        print(f"   TRANSACTION: {transaction['Date']} | {transaction['Merchant'][:30]}... | ${transaction['Amount']}")
                    else:
                        # Show potential missed transactions
                        if (len(line) > 15 and 
                            any(char.isdigit() for char in line) and 
                            ('$' in line or re.search(r'\d+\.\d{2}', line)) and
                            not any(skip in line.upper() for skip in ['TOTAL', 'BALANCE', 'PAYMENT', 'CREDIT'])):
                            print(f"❓ DEBUG: Potential transaction not parsed on line {i+1}: '{line[:80]}...'")
                
                except Exception as e:
                    print(f"🚨 DEBUG: Error on line {i+1}: {e}")
                    continue
        
        except Exception as e:
            print(f"🚨 DEBUG: Error parsing page {page_num}: {e}")
        
        print(f"📄 DEBUG: Page {page_num} completed - {len(transactions)} transactions")
        print(f"📄 DEBUG: Global cardholder after page {page_num}: '{self.global_current_cardholder}'")
        return transactions

    def parse_amex_transaction_line(self, line):
        """Parse individual American Express transaction line"""
        try:
            # Step 1: Extract date (MM/DD or MM/DD/YY) from the beginning
            date_match = re.match(r'^(\d{1,2}/\d{1,2}(?:/\d{2,4})?)', line)
            if not date_match:
                return None
            
            date_part = date_match.group(1)
            remaining_text = line[date_match.end():].strip()
            
            # Step 2: Extract amount from the end (look for $XX.XX pattern)
            amount_match = re.search(r'([-]?\$?[\d,]+\.\d{2})$', remaining_text)
            if not amount_match:
                return None
            
            amount_str = amount_match.group(1)
            merchant_and_location = remaining_text[:amount_match.start()].strip()
            
            # Step 3: Clean up amount and check if it's a charge (positive)
            amount_str = amount_str.replace('$', '').replace(',', '')
            
            # Skip negative amounts (payments/credits)
            try:
                amount_value = float(amount_str)
                if amount_value <= 0:
                    return None  # Skip payments and credits
            except ValueError:
                return None  # Skip if amount can't be parsed
            
            # Step 4: Extract ONLY merchant name from the middle part
            merchant_name = self.extract_merchant_name(merchant_and_location)
            
            if not merchant_name or len(merchant_name) < 3:
                return None
            
            # Step 5: Handle date conversion
            full_date = self.convert_date(date_part)
            if not full_date:
                return None
            
            return {
                'Date': full_date,
                'Merchant': merchant_name,
                'Amount': amount_str
            }

        except Exception:
            return None