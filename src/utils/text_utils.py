import re

class TextUtils:
    """Utility functions for text processing"""
    
    @staticmethod
    def clean_text(text):
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    @staticmethod
    def extract_numbers_from_text(text):
        """Extract all numbers from text"""
        return re.findall(r'\d+', text)
    
    @staticmethod
    def remove_special_characters(text, keep_chars=""):
        """Remove special characters except those specified"""
        pattern = f"[^a-zA-Z0-9\s{re.escape(keep_chars)}]"
        return re.sub(pattern, '', text)