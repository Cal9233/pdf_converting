#!/usr/bin/env python3
"""
Fix for Chase parser to handle corrupted text
"""

def fix_doubled_text(text):
    """Fix doubled characters in text like 'MMaannaaggee' -> 'Manage'"""
    result = []
    i = 0
    while i < len(text):
        if i + 1 < len(text) and text[i] == text[i + 1]:
            result.append(text[i])
            i += 2  # Skip the duplicate
        else:
            result.append(text[i])
            i += 1
    return ''.join(result)

def parse_chase_pdf_fixed(pdf_path):
    """Parse Chase PDF with doubled character fix"""
    import pdfplumber
    import re
    from datetime import datetime
    
    transactions = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            
            # Fix doubled characters
            text = fix_doubled_text(text)
            lines = text.split('\n')
            
            for line in lines:
                # Chase transaction pattern: MM/DD Description Amount
                # Example: 07/23 WINGSTOP 438 562-072-9341 CA -193.76
                match = re.match(r'^(\d{2}/\d{2})\s+(.+?)\s+([-]?\d+\.\d{2})$', line)
                if match:
                    date = match.group(1) + '/24'  # Add year
                    description = match.group(2).strip()
                    amount = match.group(3).replace('-', '')  # Remove negative sign
                    
                    # Skip if description contains certain patterns
                    if 'Payment Thank You' in description:
                        continue
                    
                    transactions.append({
                        'Date': date,
                        'Description': description,
                        'Amount': amount,
                        'Cardholder': 'CHASE CARDHOLDER'  # Default since not in PDF
                    })
    
    return transactions

# Test it
if __name__ == "__main__":
    trans = parse_chase_pdf_fixed('Convert/chase/20240823-statements-3488-.pdf')
    print(f"Found {len(trans)} transactions")
    for t in trans[:5]:
        print(f"  {t['Date']} - {t['Description'][:40]}... ${t['Amount']}")