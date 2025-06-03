"""
Base parser class for PDF to Excel Converter

This module provides the abstract base class for all statement parsers.
"""

import os
from abc import ABC, abstractmethod


class BaseParser(ABC):
    """Abstract base class for all statement parsers"""
    
    def __init__(self):
        pass
    
    def detect_statement_type(self, text, filename):
        """Detect if the PDF is American Express or Chase"""
        try:
            text_upper = text.upper()
            filename_upper = filename.upper()
            
            # Check filename first for more reliable detection
            if 'AMEX' in filename_upper or 'AMERICAN' in filename_upper:
                return 'amex'
            elif 'CHASE' in filename_upper:
                return 'chase'
            
            # Fallback to content detection
            if 'AMERICAN EXPRESS' in text_upper or 'AMAZON BUSINESS PRIME CARD' in text_upper:
                return 'amex'
            elif 'CHASE' in text_upper and ('ULTIMATE REWARDS' in text_upper or 'ACCOUNT ACTIVITY' in text_upper):
                return 'chase'
            else:
                return 'unknown'
        except Exception:
            return 'unknown'
    
    @abstractmethod
    def parse_page(self, page_text, page_num):
        """Parse a single page - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    def parse_transaction_line(self, line):
        """Parse a single transaction line - must be implemented by subclasses"""
        pass