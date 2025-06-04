#!/usr/bin/env python3
"""
Debug version to test PDF parsing
"""

import os
import pdfplumber
import re
from datetime import datetime

# Let's first check what PDFs we have
print("🔍 Checking PDF files...")
print("Current directory:", os.getcwd())

subdirs = ['amex', 'chase', 'w2', 'other']
for subdir in subdirs:
    path = os.path.join('Convert', subdir)
    if os.path.exists(path):
        pdfs = [f for f in os.listdir(path) if f.lower().endswith('.pdf')]
        print(f"\n{subdir}: {len(pdfs)} PDFs")
        for pdf in pdfs:
            print(f"  - {pdf}")

# Test W2 parsing
print("\n\n📄 Testing W2 parsing...")
w2_path = os.path.join('Convert', 'w2')
if os.path.exists(w2_path):
    w2_pdfs = [f for f in os.listdir(w2_path) if f.lower().endswith('.pdf')]
    if w2_pdfs:
        test_pdf = os.path.join(w2_path, w2_pdfs[0])
        print(f"Testing: {test_pdf}")
        
        with pdfplumber.open(test_pdf) as pdf:
            print(f"Pages: {len(pdf.pages)}")
            
            # Extract first page text
            if pdf.pages:
                text = pdf.pages[0].extract_text()
                lines = text.split('\n')
                
                print(f"\nFirst 20 lines of PDF:")
                for i, line in enumerate(lines[:20]):
                    print(f"{i:3d}: {line}")
                
                # Look for key W2 fields
                print("\n🔍 Looking for W2 fields...")
                
                # Find SSNs
                ssn_pattern = r'(\d{3}-\d{2}-\d{4})'
                ssns_found = []
                for i, line in enumerate(lines):
                    if 'social security number' in line.lower():
                        print(f"\nFound 'social security number' at line {i}: {line}")
                        if i + 1 < len(lines):
                            print(f"Next line: {lines[i+1]}")
                            ssn_match = re.search(ssn_pattern, lines[i + 1])
                            if ssn_match:
                                ssns_found.append(ssn_match.group(1))
                                print(f"✓ SSN found: {ssn_match.group(1)}")
                
                print(f"\nTotal SSNs found: {len(ssns_found)}")
                
                # Look for employee names
                for i, line in enumerate(lines):
                    if "employee's first name" in line.lower():
                        print(f"\nFound 'employee's first name' at line {i}: {line}")
                        if i + 1 < len(lines):
                            print(f"Next line: {lines[i+1]}")
                
                # Look for employer names
                for i, line in enumerate(lines):
                    if "employer's name" in line.lower():
                        print(f"\nFound 'employer's name' at line {i}: {line}")
                        if i + 1 < len(lines):
                            print(f"Next line: {lines[i+1]}")

# Test AmEx parsing
print("\n\n📄 Testing AmEx parsing...")
amex_path = os.path.join('Convert', 'amex')
if os.path.exists(amex_path):
    amex_pdfs = [f for f in os.listdir(amex_path) if f.lower().endswith('.pdf')]
    if amex_pdfs:
        test_pdf = os.path.join(amex_path, amex_pdfs[0])
        print(f"Testing: {test_pdf}")
        
        with pdfplumber.open(test_pdf) as pdf:
            print(f"Pages: {len(pdf.pages)}")
            
            # Extract first page text
            if pdf.pages:
                text = pdf.pages[0].extract_text()
                lines = text.split('\n')
                
                print(f"\nFirst 30 lines of PDF:")
                for i, line in enumerate(lines[:30]):
                    print(f"{i:3d}: {line}")
                
                # Look for transactions
                print("\n🔍 Looking for transactions...")
                trans_count = 0
                for i, line in enumerate(lines):
                    # AmEx date pattern
                    if re.match(r'^(\d{2}/\d{2}/\d{2})', line):
                        print(f"\nPotential transaction at line {i}: {line}")
                        trans_count += 1
                        # Check next few lines for cardholder
                        for j in range(i+1, min(i+4, len(lines))):
                            print(f"  Line {j}: {lines[j]}")
                        if trans_count >= 3:  # Just show first 3
                            break