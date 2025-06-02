"""
Date utility functions for PDF to Excel Converter

This module provides date conversion and handling utilities for processing
PDF statements with various date formats.
"""

from datetime import datetime
from config import TWO_DIGIT_YEAR_CUTOFF  # 50


class DateUtils:
    """Utility functions for date handling and conversion"""
    
    @staticmethod
    def convert_date(date_str):
        """Convert date string to full format"""
        try:
            if '/' in date_str:
                date_components = date_str.split('/')
                if len(date_components) == 3:
                    # Full date with year (MM/DD/YY)
                    month, day, year = date_components
                    if len(year) == 2:
                        # Convert 2-digit year to 4-digit year using config cutoff
                        year_num = int(year)
                        if year_num >= TWO_DIGIT_YEAR_CUTOFF:  # Years >= 50 = 19xx
                            full_year = f"19{year_num}"
                        else:  # Years < 50 = 20xx
                            full_year = f"20{year_num}"
                        return f"{month}/{day}/{full_year}"
                    else:
                        return date_str
                elif len(date_components) == 2:
                    # MM/DD format - use current year
                    current_year = datetime.now().year
                    return f"{date_str}/{current_year}"
        except Exception:
            pass
        
        return None
    
    @staticmethod
    def convert_chase_date_to_full(date_str):
        """Convert MM/DD/YY to MM/DD/YYYY"""
        try:
            parts = date_str.split('/')
            if len(parts) == 3:
                month, day, year = parts
                if len(year) == 2:
                    year_num = int(year)
                    if year_num >= TWO_DIGIT_YEAR_CUTOFF:  # Years >= 50 = 19xx
                        full_year = f"19{year_num}"
                    else:  # Years < 50 = 20xx
                        full_year = f"20{year_num}"
                    return f"{month}/{day}/{full_year}"
                else:
                    return date_str
        except Exception:
            pass
        return date_str
    
    @staticmethod
    def get_chase_transaction_year(transaction_month, chase_date_range):
        """Determine the correct year for a Chase transaction based on the date range"""
        try:
            if not chase_date_range:
                # Fallback to current year
                return datetime.now().year
            
            start_month = chase_date_range['start_month']
            end_month = chase_date_range['end_month']
            start_year = chase_date_range['start_year']
            end_year = chase_date_range['end_year']
            
            # Handle year boundary cases (e.g., 12/24/24 - 01/23/25)
            if start_year != end_year:
                if transaction_month >= start_month:
                    return start_year
                else:
                    return end_year
            else:
                # Same year for all transactions
                return start_year
                
        except Exception:
            return datetime.now().year