import sys
sys.path.insert(0, '/var/www/cal.lueshub.com/pdf_converting/Older_program')

import pdfplumber
from src.parsers.chase_parser import ChaseParser

pdf_path = "/var/www/cal.lueshub.com/pdf_converting/Older_program/Convert/chase/20240823-statements-3488-.pdf"

parser = ChaseParser()

with pdfplumber.open(pdf_path) as pdf:
    # Get full text for setup
    full_text = ""
    for page in pdf.pages:
        page_text = page.extract_text()
        if page_text:
            full_text += page_text + "\n"
    
    # Setup parser
    parser.primary_account_holder = "LUIS RODRIGUEZ"  # Manually set since extraction failed
    parser.current_cardholder = "LUIS RODRIGUEZ"
    parser.chase_date_range = parser.extract_chase_date_range(full_text)
    
    # Check pages 3-5 where transactions typically are
    for page_num in range(2, min(5, len(pdf.pages))):
        print(f"\n=== PAGE {page_num + 1} ===")
        page_text = pdf.pages[page_num].extract_text()
        
        # Show first 30 lines
        lines = page_text.split('\n')
        for i, line in enumerate(lines[:30]):
            print(f"{i+1:3}: {line[:100]}...")
        
        # Parse transactions
        transactions = parser.parse_page(page_text, page_num + 1)
        print(f"\nExtracted {len(transactions)} transactions")
        
        if transactions:
            print("\nFirst 5 transactions:")
            for i, trans in enumerate(transactions[:5]):
                print(f"{i+1}. {trans['Date']} | {trans['Name']} | {trans['Merchant'][:40]}... | ${trans['Amount']}")