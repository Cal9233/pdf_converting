"""Base transaction parser with common functionality."""

import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pdfplumber

from config.settings import (
    VALID_CARDHOLDERS, BUSINESS_INDICATORS, 
    DATE_FORMATS, AMOUNT_PATTERN
)


class TransactionParser:
    """Base parser for extracting transactions from PDF statements."""
    
    def __init__(self):
        self.current_cardholder = None
        self.transactions = []
        
    def parse_pdf(self, pdf_path: str) -> List[Dict[str, str]]:
        """Parse PDF and extract transactions."""
        self.transactions = []
        self.current_cardholder = None
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                self._parse_page(page, page_num)
                
        return self.transactions
    
    def _parse_page(self, page, page_num: int):
        """Parse a single page - to be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement _parse_page")
    
    def _extract_cardholder_name(self, text: str) -> Optional[str]:
        """Extract cardholder name if it's valid."""
        # Clean the text
        text = text.strip()
        
        # Check if it's in our valid cardholders list
        if text in VALID_CARDHOLDERS:
            return text
            
        # Check for partial matches (for variations)
        for valid_name in VALID_CARDHOLDERS:
            if valid_name in text:
                return valid_name
                
        return None
    
    def _is_business_name(self, text: str) -> bool:
        """Check if text contains business indicators."""
        text_upper = text.upper()
        for indicator in BUSINESS_INDICATORS:
            if indicator in text_upper:
                return True
        return False
    
    def _parse_date(self, text: str) -> Optional[str]:
        """Try to parse date from text."""
        # Extract potential date patterns
        date_pattern = r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
        match = re.search(date_pattern, text)
        
        if match:
            date_str = match.group()
            for fmt in DATE_FORMATS:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    return date_obj.strftime('%m/%d/%Y')
                except ValueError:
                    continue
                    
        return None
    
    def _parse_amount(self, text: str) -> Optional[float]:
        """Extract amount from text."""
        # Look for amount pattern
        matches = re.findall(AMOUNT_PATTERN, text)
        
        for match in reversed(matches):  # Check from right to left
            # Clean and convert
            amount_str = match.replace('$', '').replace(',', '')
            try:
                return float(amount_str)
            except ValueError:
                continue
                
        return None
    
    def _clean_merchant_name(self, merchant: str) -> str:
        """Clean up merchant name - extract just the business name."""
        # Remove extra spaces
        merchant = ' '.join(merchant.split())
        
        # Keep original for fallback
        original = merchant
        
        # Special prefixes for payment processors (do this first)
        if merchant.startswith('TST* '):
            merchant = merchant[5:].strip()
        elif merchant.startswith('TST*'):
            merchant = merchant[4:].strip()
        elif merchant.startswith('SPO*'):
            merchant = merchant[4:].strip()
        elif merchant.startswith('SQ *'):
            merchant = merchant[4:].strip()
        
        # Remove everything after common patterns that indicate location/extra info
        # Look for patterns that typically start location/contact info
        
        # Remove everything after a long number (like 545500001584499)
        merchant = re.sub(r'\s+\d{12,}.*$', '', merchant)
        
        # Remove everything after phone numbers: 415-555-1234, 415-5551234, or 4155551234
        merchant = re.sub(r'\s+\d{3}[-.]?\d{3}[-.]?\d{4}.*$', '', merchant)
        
        # Remove everything after URLs: help.uber.com, gosq.com
        merchant = re.sub(r'\s+\w+\.\w+\.?\w*.*$', '', merchant)
        
        # Remove everything after city names (when followed by state or more text)
        cities = '(San Francisco|San Jose|San Bruno|San Mateo|Daly City|South San Fra|Burlingame|Vallejo|Oakland|Berkeley|Sacramento|Los Angeles|Las Vegas|West Hollywood|West Hollywoo)'
        merchant = re.sub(rf'\s+{cities}.*$', '', merchant, flags=re.IGNORECASE)
        
        # Remove standalone state abbreviations at the very end
        merchant = re.sub(r'\s+[A-Z]{2}$', '', merchant)
        
        # Remove store/location numbers at the very end
        merchant = re.sub(r'\s+#\d{3,5}$', '', merchant)
        merchant = re.sub(r'\s+\d{4,10}$', '', merchant)  # Store numbers like 000005529
        
        # Clean up specific patterns
        merchant = re.sub(r'\s+-\s+\w+$', '', merchant)  # "BIERGARTEN - SAN FRA"
        
        # Final cleanup
        merchant = merchant.strip()
        
        # If we ended up with nothing or very short, use original
        if not merchant or len(merchant) < 3:
            merchant = original.split()[0] if original.split() else original
            
        return merchant