import sys
sys.path.insert(0, '/var/www/cal.lueshub.com/pdf_converting/Older_program')

import pdfplumber
from src.parsers.chase_parser import ChaseParser

# Test the Chase parser from Older_program
pdf_path = "/var/www/cal.lueshub.com/pdf_converting/Older_program/Convert/chase/20240823-statements-3488-.pdf"

parser = ChaseParser()

# Extract full text
with pdfplumber.open(pdf_path) as pdf:
    full_text = ""
    for page in pdf.pages[:2]:  # Just first 2 pages
        page_text = page.extract_text()
        if page_text:
            full_text += page_text + "\n"
    
    print("=== Testing Primary Account Holder Extraction ===")
    primary_name = parser.extract_primary_account_holder(full_text)
    print(f"Primary account holder: '{primary_name}'")
    
    print("\n=== Testing Date Range Extraction ===")
    date_range = parser.extract_chase_date_range(full_text)
    print(f"Date range: {date_range}")
    
    # Process first page
    print("\n=== Processing Page 1 ===")
    parser.primary_account_holder = primary_name
    parser.current_cardholder = primary_name
    parser.chase_date_range = date_range
    
    page1_text = pdf.pages[0].extract_text()
    transactions = parser.parse_page(page1_text, 1)
    
    print(f"\nExtracted {len(transactions)} transactions from page 1")
    if transactions:
        print("\nFirst 5 transactions:")
        for i, trans in enumerate(transactions[:5]):
            print(f"{i+1}. {trans['Date']} | {trans['Name']} | {trans['Merchant'][:40]}... | ${trans['Amount']}")