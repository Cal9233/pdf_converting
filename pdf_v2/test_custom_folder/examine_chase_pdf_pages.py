import pdfplumber

pdf_path = "/var/www/cal.lueshub.com/pdf_converting/Older_program/Convert/chase/20240823-statements-3488-.pdf"

with pdfplumber.open(pdf_path) as pdf:
    for page_num in range(min(3, len(pdf.pages))):
        page = pdf.pages[page_num]
        text = page.extract_text()
        
        print(f"\n=== PAGE {page_num + 1} ===")
        lines = text.split('\n')
        
        # Look for transaction patterns or cardholder names
        for i, line in enumerate(lines):
            # Skip empty or very short lines
            if len(line.strip()) < 5:
                continue
                
            # Look for date patterns at start of line
            if line[:5].count('/') == 2:
                print(f"Line {i+1}: {line[:80]}...")
            
            # Look for potential names (all caps, 2-4 words)
            words = line.strip().split()
            if (2 <= len(words) <= 4 and 
                line.strip().isupper() and 
                not any(char.isdigit() for char in line) and
                len(line.strip()) <= 40):
                print(f"POTENTIAL NAME Line {i+1}: {line.strip()}")
            
            # Look for "TRANSACTIONS THIS CYCLE"
            if "TRANSACTIONS THIS CYCLE" in line.upper():
                print(f"HEADER Line {i+1}: {line[:80]}...")
                # Show previous 5 lines
                for j in range(max(0, i-5), i):
                    print(f"  Before ({j+1}): {lines[j][:80]}...")