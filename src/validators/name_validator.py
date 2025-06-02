"""
Name validation and extraction utilities for PDF statement processing.

This module provides validation logic for cardholder names from both
AmEx and Chase statements, including merchant name extraction.
"""

import re
from config import (
    VALID_NAME_PARTS,
    AMEX_FALSE_POSITIVES,
    CHASE_FALSE_POSITIVES,
    BUSINESS_TERMS
)

class NameValidator:
    """Validates and extracts cardholder names from statements"""
    
    def __init__(self):
        """Initialize the name validator"""
        pass

    def extract_merchant_name(self, text):
        """Extract only the merchant name, excluding location and personal info"""
        try:
            # Remove common prefixes
            text = re.sub(r'^(AplPay|TST\*|SQ \*)', '', text).strip()
            
            # Split by common delimiters and patterns
            words = text.split()
            merchant_parts = []
            
            for word in words:
                # Stop at common location indicators
                if (word.upper() in ['CA', 'NY', 'TX', 'FL', 'WA', 'OR', 'NV', 'AZ'] or  # State codes
                    re.match(r'^\d{3}-\d{3}-\d{4}$', word) or  # Phone numbers
                    re.match(r'^\d{10,}$', word) or  # Long numbers
                    word.lower().endswith('.com') or  # Websites
                    word.lower().endswith('.net') or
                    word.lower().endswith('.org') or
                    len(word) > 20):  # Very long words (likely IDs or URLs)
                    break
                
                # Add word to merchant name if it looks valid
                if (len(word) >= 2 and 
                    not word.isdigit() and 
                    word.upper() not in ['AND', 'THE', 'OF', 'IN', 'AT', 'FOR']):
                    merchant_parts.append(word)
            
            # Join the merchant parts
            merchant_name = ' '.join(merchant_parts)
            
            # Clean up common patterns
            merchant_name = re.sub(r'\s+', ' ', merchant_name)  # Multiple spaces
            merchant_name = re.sub(r'[#*]+.*$', '', merchant_name)  # Remove # and * suffixes
            merchant_name = merchant_name.strip()
            
            # Additional cleanup for specific patterns
            merchant_name = re.sub(r'\s+\d{3,}$', '', merchant_name)
            
            return merchant_name
        
        except Exception:
            return ""
        
    def is_continuation_header(self, line):
        """Check if line is a continuation header"""
        try:
            line_upper = line.strip().upper()
            
            continuation_patterns = [
                'DETAIL CONTINUED',
                'CONTINUED ON NEXT PAGE',
                'CONTINUED ON REVERSE',
                'ACCOUNT ACTIVITY (CONTINUED)',
                'ACCOUNT ACTIVITY CONTINUED',
                'TRANSACTIONS THIS CYCLE',
                'INCLUDING PAYMENTS RECEIVED',
                'CONTINUED FROM PREVIOUS PAGE',
                'AMOUNT'
            ]
            
            for pattern in continuation_patterns:
                if pattern in line_upper:
                    return True
            
            # Check for account ending lines in continuation sections
            if ('ACCOUNT ENDING' in line_upper and 
                len(line.split()) >= 3 and 
                any(char.isdigit() for char in line)):
                return True
            
            return False
            
        except Exception:
            return False
        
    def extract_cardholder_name(self, line):
        """Extract cardholder name with enhanced debugging"""
        try:
            line = line.strip()
            
            print(f"🔍 DEBUG: Analyzing line: '{line}'")
            
            # Skip continuation headers first
            if self.is_continuation_header(line):
                print(f"   🔄 SKIPPED: Continuation header")
                return None
            
            # Skip lines with obvious non-name content
            skip_patterns = [
                'Amount', '$', 'Date', 'Merchant', 'Transaction', 'Account', 'Page',
                'Statement', 'Balance', 'Payment', 'Interest', 'Fee', 'Charge',
                'Credit', 'Debit', 'Purchase', 'Cash', 'Advance', 'Transfer',
                'www.', 'http', '.com', '@', '#', '*', '&', '%', 
                'Detail', 'Continued', 'Including', 'Payments', 'Received',
                '/', '-', '(', ')', '[', ']', '{', '}', '|', '\\'
            ]
            
            skip_found = [pattern for pattern in skip_patterns if pattern in line]
            if skip_found:
                print(f"   ⏭️  SKIPPED: Contains: {skip_found}")
                return None
            
            # Pattern 1: "NAME Card Ending X-XXXXX"
            if 'Card Ending' in line:
                print(f"   📋 Pattern 1: Card Ending found")
                
                if any(word in line.upper() for word in ['CONTINUED', 'DETAIL', 'INCLUDING']):
                    print(f"   ⏭️  SKIPPED: In continuation context")
                    return None
                
                parts = line.split('Card Ending')
                if parts:
                    potential_name = parts[0].strip()
                    print(f"   🔎 Extracted: '{potential_name}'")
                    if self.is_valid_cardholder_name(potential_name):
                        print(f"   ✅ VALID: '{potential_name}' (Pattern 1)")
                        return potential_name
                    else:
                        print(f"   ❌ INVALID: '{potential_name}'")
            
            # Pattern 2: Standalone name lines
            words = line.split()
            if (2 <= len(words) <= 3 and 
                line.isupper() and 
                len(line) <= 30 and
                not any(char.isdigit() for char in line)):
                
                print(f"   📋 Pattern 2: Standalone name candidate")
                
                if any(word in line.upper() for word in ['CONTINUED', 'DETAIL', 'INCLUDING', 'AMOUNT']):
                    print(f"   ⏭️  SKIPPED: Near continuation keywords")
                    return None
                
                if self.is_valid_cardholder_name(line):
                    print(f"   ✅ VALID: '{line}' (Pattern 2)")
                    return line.strip()
                else:
                    print(f"   ❌ INVALID: '{line}'")
            
            # Pattern 3: Name + account info
            if len(words) >= 3:
                print(f"   📋 Pattern 3: Name + account info")
                
                if any(word in line.upper() for word in ['CONTINUED', 'DETAIL', 'INCLUDING']):
                    print(f"   ⏭️  SKIPPED: In continuation context")
                    return None
                
                # Try 2-word names
                potential_name = ' '.join(words[:2])
                remaining = ' '.join(words[2:]).upper()
                account_keywords = ['CARD', 'ACCOUNT', 'ENDING', 'AMOUNT']
                found_keywords = [kw for kw in account_keywords if kw in remaining]
                
                if self.is_valid_cardholder_name(potential_name) and found_keywords:
                    print(f"   ✅ VALID: '{potential_name}' (Pattern 3)")
                    return potential_name
                
                # Try 3-word names
                if len(words) >= 4:
                    potential_name = ' '.join(words[:3])
                    remaining = ' '.join(words[3:]).upper()
                    found_keywords = [kw for kw in account_keywords if kw in remaining]
                    
                    if self.is_valid_cardholder_name(potential_name) and found_keywords:
                        print(f"   ✅ VALID: '{potential_name}' (Pattern 3)")
                        return potential_name
            
            print(f"   ❌ NO NAME FOUND")
            return None
                                
        except Exception as e:
            print(f"   🚨 ERROR: {e}")
            return None
        
    def is_valid_cardholder_name(self, name):
        """Enhanced name validation with detailed logging"""
        try:
            if not name or len(name.strip()) < 3:
                print(f"      🔍 VALIDATION: '{name}' - TOO SHORT")
                return False
                
            name = name.strip()
            words = name.split()
            
            if len(words) < 2 or len(words) > 4:
                print(f"      🔍 VALIDATION: '{name}' - WRONG WORD COUNT ({len(words)})")
                return False
            
            if not name.isupper():
                print(f"      🔍 VALIDATION: '{name}' - NOT UPPERCASE")
                return False
            
            # Check alphabetic characters
            # Check alphabetic characters
            for word in words:
                if not (word.isalpha() or word in VALID_NAME_PARTS):  # ✅ Use config
                    print(f"      🔍 VALIDATION: '{name}' - NON-ALPHA: {word}")
                    return False
            
            # Check word lengths
            for word in words:
                if len(word) < 2 or len(word) > 15:
                    print(f"      🔍 VALIDATION: '{name}' - BAD LENGTH: {word}")
                    return False
            
            # Check for vowels in short words (avoid acronyms)
            for word in words:
                if len(word) <= 3 and not any(vowel in word for vowel in 'AEIOU'):
                    print(f"      🔍 VALIDATION: '{name}' - NO VOWELS: {word}")
                    return False
            
            for fp in AMEX_FALSE_POSITIVES:
                if fp in name.upper():
                    print(f"      🔍 VALIDATION: '{name}' - FALSE POSITIVE: {fp}")
                    return False
            
            # Business terms
            for word in words:
                if word in BUSINESS_TERMS: 
                    print(f"      🔍 VALIDATION: '{name}' - BUSINESS TERM: {word}")
                    return False
            
            print(f"      ✅ VALIDATION: '{name}' - PASSED")
            return True
            
        except Exception as e:
            print(f"      🚨 VALIDATION ERROR: {e}")
            return False
        
    def is_valid_chase_cardholder_name(self, name):
        """Validate if a string is likely a Chase cardholder name"""
        try:
            if not name or len(name.strip()) < 3:
                print(f"      🔍 CHASE VALIDATION: '{name}' - TOO SHORT")
                return False
                
            name = name.strip()
            words = name.split()
            
            # Must have at least 2 words (first and last name)
            if len(words) < 2 or len(words) > 5:  # Chase allows slightly longer names
                print(f"      🔍 CHASE VALIDATION: '{name}' - WRONG WORD COUNT ({len(words)})")
                return False
            
            # Must be all uppercase (Chase format)
            if not name.isupper():
                print(f"      🔍 CHASE VALIDATION: '{name}' - NOT UPPERCASE")
                return False
            
            # Each word should be alphabetic (with exceptions)
            for word in words:
                if not (word.isalpha() or word in VALID_NAME_PARTS): 
                    print(f"      🔍 CHASE VALIDATION: '{name}' - NON-ALPHA: {word}")
                    return False
            
            # Check word lengths
            for word in words:
                if len(word) < 2 or len(word) > 15:
                    print(f"      🔍 CHASE VALIDATION: '{name}' - BAD LENGTH: {word}")
                    return False
            
            # Check for vowels in short words
            for word in words:
                if len(word) <= 3 and not any(vowel in word for vowel in 'AEIOU'):
                    print(f"      🔍 CHASE VALIDATION: '{name}' - NO VOWELS: {word}")
                    return False
            
            # Chase-specific false positives
            for fp in CHASE_FALSE_POSITIVES:
                if fp in name.upper():
                    print(f"      🔍 CHASE VALIDATION: '{name}' - FALSE POSITIVE: {fp}")
                    return False
            
            # Business terms specific to Chase statements
            for word in words:
                if word in BUSINESS_TERMS:
                    print(f"      🔍 CHASE VALIDATION: '{name}' - BUSINESS TERM: {word}")
                    return False
            
            print(f"      ✅ CHASE VALIDATION: '{name}' - PASSED")
            return True
            
        except Exception as e:
            print(f"      🚨 CHASE VALIDATION ERROR: {e}")
            return False

    def extract_chase_cardholder_name(self, current_line, all_lines, current_index):
        """Enhanced Chase cardholder name extraction with better debugging"""
        try:
            print(f"🔍 DEBUG: Checking Chase name pattern on line {current_index + 1}: '{current_line}'")
            
            # Pattern 1: Look for "TRANSACTIONS THIS CYCLE (CARD XXXX)" pattern
            if 'TRANSACTIONS THIS CYCLE' in current_line.upper() and 'CARD' in current_line.upper():
                print(f"   📋 Found TRANSACTIONS THIS CYCLE pattern")
                
                # Extract card number for validation
                card_match = re.search(r'CARD\s+(\d+)', current_line.upper())
                if card_match:
                    card_number = card_match.group(1)
                    print(f"   💳 Card number found: {card_number}")
                
                # The name should be on the previous line(s)
                potential_name = None
                
                # Check previous line for name
                if current_index > 0:
                    prev_line = all_lines[current_index - 1].strip()
                    print(f"   🔎 Checking previous line for name: '{prev_line}'")
                    
                    if self.is_valid_chase_cardholder_name(prev_line):
                        potential_name = prev_line.strip()
                        print(f"   ✅ VALID CHASE NAME: '{potential_name}' (from previous line)")
                        return potential_name
                    else:
                        print(f"   ❌ Previous line failed validation: '{prev_line}'")
                
                # Check 2 lines back in case there's a blank line
                if current_index > 1:
                    prev_prev_line = all_lines[current_index - 2].strip()
                    print(f"   🔎 Checking 2 lines back for name: '{prev_prev_line}'")
                    
                    if self.is_valid_chase_cardholder_name(prev_prev_line):
                        potential_name = prev_prev_line.strip()
                        print(f"   ✅ VALID CHASE NAME: '{potential_name}' (from 2 lines back)")
                        return potential_name
                    else:
                        print(f"   ❌ 2 lines back failed validation: '{prev_prev_line}'")
                
                # Check 3 lines back
                if current_index > 2:
                    prev_prev_prev_line = all_lines[current_index - 3].strip()
                    print(f"   🔎 Checking 3 lines back for name: '{prev_prev_prev_line}'")
                    
                    if self.is_valid_chase_cardholder_name(prev_prev_prev_line):
                        potential_name = prev_prev_prev_line.strip()
                        print(f"   ✅ VALID CHASE NAME: '{potential_name}' (from 3 lines back)")
                        return potential_name
            
            # Pattern 2: Look for name followed by "TRANSACTIONS THIS CYCLE" on the SAME line
            if 'TRANSACTIONS THIS CYCLE' in current_line.upper():
                # Split by "TRANSACTIONS" to get the name part
                parts = current_line.split('TRANSACTIONS THIS CYCLE')
                if len(parts) > 0:
                    potential_name = parts[0].strip()
                    print(f"   🔎 Extracted name from same line: '{potential_name}'")
                    
                    if self.is_valid_chase_cardholder_name(potential_name):
                        print(f"   ✅ VALID CHASE NAME: '{potential_name}' (same line)")
                        return potential_name
                    else:
                        print(f"   ❌ Same line name failed validation: '{potential_name}'")
            
            # Pattern 3: Look for isolated name lines
            if (len(current_line.split()) >= 2 and 
                len(current_line.split()) <= 4 and
                current_line.isupper() and
                not any(char.isdigit() for char in current_line) and
                len(current_line) <= 40):
                
                print(f"   📋 Checking isolated name candidate: '{current_line}'")
                
                # Check if the next few lines contain "TRANSACTIONS THIS CYCLE" or transaction patterns
                found_supporting_evidence = False
                for check_ahead in range(1, 8):  # Check next 7 lines
                    if current_index + check_ahead < len(all_lines):
                        future_line = all_lines[current_index + check_ahead]
                        if ('TRANSACTIONS THIS CYCLE' in future_line.upper() or
                            # Look for transaction patterns (date + amount)
                            (re.search(r'^\d{1,2}/\d{1,2}', future_line) and re.search(r'\d+\.\d{2}$', future_line))):
                            found_supporting_evidence = True
                            print(f"   📊 Found supporting evidence {check_ahead} lines ahead: '{future_line[:50]}...'")
                            break
                
                if found_supporting_evidence and self.is_valid_chase_cardholder_name(current_line):
                    print(f"   ✅ VALID CHASE NAME: '{current_line}' (isolated, with supporting evidence)")
                    return current_line.strip()
                elif found_supporting_evidence:
                    print(f"   ❌ Isolated name failed validation: '{current_line}'")
            
            print(f"   ❌ NO CHASE NAME FOUND")
            return None
            
        except Exception as e:
            print(f"   🚨 ERROR in extract_chase_cardholder_name: {e}")
            return None
