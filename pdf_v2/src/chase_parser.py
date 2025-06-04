"""Parser for Chase PDF statements."""

import re
from typing import Dict, List, Optional

from src.transaction_parser import TransactionParser


class ChaseParser(TransactionParser):
    """Parser specifically for Chase statements."""
    
    def _parse_page(self, page, page_num: int):
        """Parse a Chase statement page."""
        text = page.extract_text()
        if not text:
            return
            
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Check for cardholder name sections
            if self._is_potential_cardholder_line(line, lines, i):
                name = self._extract_cardholder_name(line)
                if name:
                    self.current_cardholder = name
                    continue
            
            # Parse transaction lines
            transaction = self._parse_transaction_line(line)
            if transaction and self.current_cardholder:
                transaction['Name'] = self.current_cardholder
                self.transactions.append(transaction)
    
    def _is_potential_cardholder_line(self, line: str, lines: List[str], index: int) -> bool:
        """Check if this line might contain a cardholder name."""
        # Chase specific patterns
        
        # Pattern 1: Line before "Account Number:"
        if index < len(lines) - 1:
            next_line = lines[index + 1].strip()
            if 'Account Number:' in next_line or 'ACCOUNT NUMBER:' in next_line:
                # This line might be the cardholder name
                if line.strip() and not self._is_business_name(line):
                    return True
                    
        # Pattern 2: Section headers with names (often in all caps)
        if line.isupper() and 2 <= len(line.split()) <= 4:
            # Check if it's followed by transaction-related content
            if index < len(lines) - 2:
                next_lines = [lines[i].strip() for i in range(index + 1, min(index + 3, len(lines)))]
                if any('Transaction' in l or 'Payment' in l or 'Purchase' in l for l in next_lines):
                    return not self._is_business_name(line)
                    
        # Pattern 3: Check for name patterns in specific contexts
        if index < len(lines) - 1:
            # Look for patterns like "FIRSTNAME LASTNAME" followed by account info
            words = line.strip().split()
            if 2 <= len(words) <= 3 and all(word.isalpha() for word in words):
                if not self._is_business_name(line):
                    return True
                    
        return False
    
    def _parse_transaction_line(self, line: str) -> Optional[Dict[str, str]]:
        """Parse a transaction from a line."""
        # Chase transaction patterns:
        # Pattern 1: MM/DD description amount
        # Pattern 2: MM/DD description (amount might be on next line)
        
        # First try the complete pattern
        pattern = r'^(\d{2}/\d{2})\s+(.+?)\s+(-?\$?[\d,]+\.\d{2})$'
        match = re.match(pattern, line)
        
        if match:
            date_str = match.group(1)
            merchant = match.group(2).strip()
            amount_str = match.group(3)
            
            # Add current year to date
            current_year = '2024'  # You might want to make this dynamic
            full_date = f"{date_str}/{current_year}"
            
            # Parse date
            date = self._parse_date(full_date)
            if not date:
                return None
                
            # Parse amount (handle negative amounts for credits)
            amount = self._parse_amount(amount_str.replace('-', ''))
            if amount is None:
                return None
                
            # Clean merchant name
            # Remove leading & or 8 (common in Chase statements)
            if merchant.startswith('& '):
                merchant = merchant[2:]
            elif merchant.startswith('8 '):
                merchant = merchant[2:]
                
            merchant = self._clean_merchant_name(merchant)
            
            return {
                'Date': date,
                'Merchant': merchant,
                'Amount': amount
            }
        
        # Also try pattern where date and merchant are on the line
        # This helps with Chase's multi-line transactions
        date_pattern = r'^(\d{2}/\d{2})\s+(.+?)$'
        match = re.match(date_pattern, line)
        if match and not re.search(r'\$?[\d,]+\.\d{2}$', line):
            # This might be a transaction without amount on same line
            # Store it for potential matching with next line
            # For now, skip these
            pass
            
        return None