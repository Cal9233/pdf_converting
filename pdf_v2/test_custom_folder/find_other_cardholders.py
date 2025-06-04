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
    parser.primary_account_holder = "LUIS RODRIGUEZ"
    parser.current_cardholder = "LUIS RODRIGUEZ"
    parser.chase_date_range = parser.extract_chase_date_range(full_text)
    
    # Search all pages for other cardholders
    for page_num in range(len(pdf.pages)):
        page_text = pdf.pages[page_num].extract_text()
        lines = page_text.split('\n')
        
        # Look for names of other cardholders we saw in the Excel
        other_names = ["JUAN LUIS RODRIGUEZ", "JOSE RODRIGUEZ", "RODRIGUEZ GUTIERREZ", "PULAK UNG"]
        
        for i, line in enumerate(lines):
            # Check if any of the other names appear
            for name in other_names:
                if name in line.upper():
                    print(f"\n=== Found '{name}' on page {page_num + 1}, line {i+1} ===")
                    # Show context: 5 lines before and after
                    for j in range(max(0, i-5), min(len(lines), i+6)):
                        marker = ">>> " if j == i else "    "
                        print(f"{marker}Line {j+1}: {lines[j][:100]}...")
                    
            # Also look for "TRANSACTIONS THIS CYCLE" patterns
            if "TRANSACTIONS THIS CYCLE" in line.upper() and "CARD" in line.upper():
                # Check who this section is for
                print(f"\n=== Found TRANSACTIONS section on page {page_num + 1}, line {i+1} ===")
                # Show previous 5 lines to see if there's a name
                for j in range(max(0, i-5), i+1):
                    print(f"Line {j+1}: {lines[j][:100]}...")