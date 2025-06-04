"""Parser for American Express PDF statements."""

import re
from typing import Dict, List, Optional

from src.transaction_parser import TransactionParser


class AmexParser(TransactionParser):
    """Parser specifically for AmEx statements."""
    
    def _parse_page(self, page, page_num: int):
        """Parse an AmEx statement page."""
        text = page.extract_text()
        if not text:
            return
            
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Check for cardholder name at the top of sections
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
        # AmEx patterns for cardholder sections
        if 'Account Ending' in line:
            return True
            
        # Check if it's before transaction details
        if index < len(lines) - 1:
            next_line = lines[index + 1].strip()
            if any(keyword in next_line for keyword in ['Detail', 'Transaction', 'Date']):
                return True
                
        # Check if line is all caps and short (typical for names)
        if line.isupper() and len(line.split()) <= 3 and not any(c.isdigit() for c in line):
            # But not if it contains business indicators
            if not self._is_business_name(line):
                return True
                
        return False
    
    def _parse_transaction_line(self, line: str) -> Optional[Dict[str, str]]:
        """Parse a transaction from a line."""
        # AmEx transaction pattern: MM/DD or MM/DD/YY followed by merchant and amount
        pattern = r'^(\d{2}/\d{2}(?:/\d{2})?)\s+(.+?)\s+(\$?[\d,]+\.\d{2})$'
        match = re.match(pattern, line)
        
        if match:
            date_str = match.group(1)
            merchant = match.group(2)
            amount_str = match.group(3)
            
            # Parse date
            date = self._parse_date(date_str)
            if not date:
                return None
                
            # Parse amount
            amount = self._parse_amount(amount_str)
            if amount is None:
                return None
                
            # Clean merchant name
            merchant = self._clean_merchant_name(merchant)
            
            return {
                'Date': date,
                'Merchant': merchant,
                'Amount': amount
            }
            
        return None