import re
from datetime import datetime
from .base_parser import BaseParser
from src.validators.name_validator import NameValidator

class ChaseParser(BaseParser):
    """Parser for Chase statements"""
    
    def __init__(self):
        super().__init__()
        self.name_validator = NameValidator()
        self.chase_date_range = None
        self.global_current_cardholder = "Unknown"
            
    def parse_chase_page(self, page_text, page_num):
        """Parse Chase page with enhanced name detection and debugging"""
        transactions = []
        
        print(f"\n📄 DEBUG: Starting Chase page {page_num} with global cardholder: '{getattr(self, 'global_current_cardholder', 'Unknown')}'")
        
        # Initialize global cardholder if not exists
        if not hasattr(self, 'global_current_cardholder'):
            self.global_current_cardholder = "Unknown"
        
        try:
            lines = page_text.split('\n')
            print(f"📄 DEBUG: Chase page {page_num} has {len(lines)} lines")
            
            # CHASE STRATEGY: Parse all transactions first, then assign names retroactively
            temp_transactions = []  # Store transactions without names first
            page_cardholders_found = []  # Track all cardholders found on this page
            
            for i, line in enumerate(lines):
                try:
                    line = line.strip()
                    
                    # Skip empty lines
                    if len(line) < 5:
                        continue
                    
                    # Skip headers
                    if (('Date of' in line and 'Transaction' in line) or
                        'Merchant Name' in line or
                        'ACCOUNT ACTIVITY' in line or
                        line.startswith('CHASE') or
                        line.startswith('Page') or
                        line.startswith('Customer Service')):
                        continue
                    
                    # Enhanced Chase name detection
                    cardholder_name = self.extract_chase_cardholder_name(line, lines, i)
                    if cardholder_name:
                        page_cardholders_found.append(cardholder_name)
                        print(f"🏷️  DEBUG: CHASE CARDHOLDER FOUND on line {i+1}: '{cardholder_name}'")
                        
                        # Count how many Unknown transactions we're about to assign
                        unknown_count = sum(1 for t in temp_transactions if t.get('Name') == 'Unknown')
                        print(f"   📊 Will assign '{cardholder_name}' to {unknown_count} Unknown transactions")
                        
                        # Assign this name to all previous temp_transactions that are Unknown
                        assigned_count = 0
                        for temp_trans in temp_transactions:
                            if temp_trans.get('Name') == 'Unknown':
                                temp_trans['Name'] = cardholder_name
                                assigned_count += 1
                                if assigned_count <= 3:  # Show first 3 assignments
                                    print(f"   🔄 ASSIGNED: '{cardholder_name}' to {temp_trans['Date']} {temp_trans['Merchant'][:20]}...")
                                elif assigned_count == 4:
                                    print(f"   🔄 ... and {unknown_count - 3} more transactions")
                        
                        # Update global cardholder for future transactions
                        self.global_current_cardholder = cardholder_name
                        print(f"   🌐 Updated global cardholder to: '{cardholder_name}'")
                        continue
                    
                    # Try to parse as transaction
                    transaction = self.parse_chase_transaction_line(line)
                    if transaction:
                        # For Chase, start with Unknown and assign name later
                        transaction['Name'] = 'Unknown'
                        temp_transactions.append(transaction)
                        if len(temp_transactions) % 10 == 1:  # Show every 10th transaction to avoid spam
                            print(f"💳 DEBUG: Chase transaction #{len(temp_transactions)} on line {i+1} (pending name assignment)")
                            print(f"   TRANSACTION: {transaction['Date']} | {transaction['Merchant'][:30]}... | ${transaction['Amount']}")
                    else:
                        # Enhanced debugging for potential missed transactions
                        if (len(line) > 15 and 
                            any(char.isdigit() for char in line) and 
                            ('$' in line or re.search(r'\d+\.\d{2}', line)) and
                            not any(skip in line.upper() for skip in ['TOTAL', 'BALANCE', 'PAYMENT', 'CREDIT', 'AUTOPAY', 'MINIMUM'])):
                            # Only show first few potential missed transactions to avoid spam
                            missed_shown = sum(1 for t in temp_transactions if 'potential_missed' in str(t))
                            if missed_shown < 3:
                                print(f"❓ DEBUG: Potential Chase transaction not parsed on line {i+1}: '{line[:80]}...'")
                
                except Exception as e:
                    print(f"🚨 DEBUG: Error on Chase line {i+1}: {e}")
                    continue
            
            # IMPORTANT: Final assignment for any remaining Unknown transactions
            unknown_remaining = sum(1 for t in temp_transactions if t.get('Name') == 'Unknown')
            if unknown_remaining > 0:
                print(f"📊 DEBUG: {unknown_remaining} transactions still Unknown at end of page {page_num}")
                print(f"📊 DEBUG: Current global cardholder: '{self.global_current_cardholder}'")
                print(f"📊 DEBUG: Cardholders found on this page: {page_cardholders_found}")
                
                # Use the most recent cardholder (either from this page or global)
                final_cardholder = self.global_current_cardholder
                if page_cardholders_found:
                    final_cardholder = page_cardholders_found[-1]  # Use the last one found on this page
                
                if final_cardholder != "Unknown":
                    assigned_final = 0
                    for temp_trans in temp_transactions:
                        if temp_trans.get('Name') == 'Unknown':
                            temp_trans['Name'] = final_cardholder
                            assigned_final += 1
                            if assigned_final <= 3:
                                print(f"   🔄 FINAL ASSIGNMENT: '{final_cardholder}' to {temp_trans['Date']} {temp_trans['Merchant'][:20]}...")
                            elif assigned_final == 4:
                                print(f"   🔄 ... and {unknown_remaining - 3} more final assignments")
                    
                    print(f"✅ DEBUG: Assigned {assigned_final} remaining Unknown transactions to '{final_cardholder}'")
                else:
                    print(f"⚠️  DEBUG: No cardholder available for final assignment - {unknown_remaining} transactions will remain Unknown")
            
            transactions = temp_transactions
        
        except Exception as e:
            print(f"🚨 DEBUG: Error parsing Chase page {page_num}: {e}")
        
        print(f"📄 DEBUG: Chase page {page_num} completed - {len(transactions)} transactions")
        print(f"📄 DEBUG: Global cardholder after Chase page {page_num}: '{self.global_current_cardholder}'")
        
        # Show summary of names assigned
        name_counts = {}
        for trans in transactions:
            name = trans.get('Name', 'Unknown')
            name_counts[name] = name_counts.get(name, 0) + 1
        print(f"📊 DEBUG: Name distribution on page {page_num}: {name_counts}")
        
        return transactions
    
    def parse_chase_transaction_line(self, line):
        """Parse individual Chase transaction line with enhanced debugging"""
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
                    amount_value = float(amount.replace(',', ''))  # Remove commas before parsing!
                    if amount_value <= 0:
                        return None  # Skip payments and credits
                except ValueError:
                    return None  # Skip if amount can't be parsed
                
                # Get the correct year based on the date range
                transaction_month = int(date.split('/')[0])
                correct_year = self.get_chase_transaction_year(transaction_month)
                full_date = f"{date}/{correct_year}"
                
                return {
                    'Date': full_date,
                    'Merchant': merchant_desc,
                    'Amount': amount
                }
        
        except Exception:
            pass
        
        return None