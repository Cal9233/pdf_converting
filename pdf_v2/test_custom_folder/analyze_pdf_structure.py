#!/usr/bin/env python3
"""
Analyze PDF structure to understand parsing issues
"""

import pdfplumber
import re

# Analyze W2 PDF
print("🔍 Analyzing W2 PDF structure...")
with pdfplumber.open('Convert/w2/2024 - Forms W-2 & W3 - EMPLOYER COPY - Ocomar Enterprises.pdf') as pdf:
    # Look at first page in detail
    page = pdf.pages[0]
    text = page.extract_text()
    lines = text.split('\n')
    
    print(f"\n📄 Page 1 - Total lines: {len(lines)}")
    
    # Find employee name section
    for i, line in enumerate(lines[:50]):
        if 'employee' in line.lower() and 'name' in line.lower():
            print(f"\n✓ Found employee name label at line {i}: '{line}'")
            print("  Next 8 lines:")
            for j in range(i+1, min(i+9, len(lines))):
                print(f"    {j}: '{lines[j]}'")
    
    # Find employer name section  
    for i, line in enumerate(lines[:50]):
        if 'employer' in line.lower() and 'name' in line.lower():
            print(f"\n✓ Found employer name label at line {i}: '{line}'")
            print("  Next 5 lines:")
            for j in range(i+1, min(i+6, len(lines))):
                print(f"    {j}: '{lines[j]}'")
    
    # Find wages section
    for i, line in enumerate(lines[:50]):
        if 'wages' in line.lower() and 'tips' in line.lower():
            print(f"\n✓ Found wages label at line {i}: '{line}'")
            print("  Full line content:")
            print(f"    '{line}'")

# Now test AmEx
print("\n\n🔍 Analyzing AmEx PDF structure...")
with pdfplumber.open('Convert/amex/2024-12-09.pdf') as pdf:
    # Skip to page with transactions (usually page 2)
    if len(pdf.pages) > 1:
        page = pdf.pages[1]
        text = page.extract_text()
        lines = text.split('\n')
        
        print(f"\n📄 Page 2 - Looking for transactions...")
        trans_found = 0
        for i, line in enumerate(lines):
            # Look for MM/DD pattern
            if re.match(r'^\d{2}/\d{2}', line):
                print(f"\n✓ Transaction at line {i}: '{line}'")
                # Show context
                if i > 0:
                    print(f"  Previous: '{lines[i-1]}'")
                if i + 1 < len(lines):
                    print(f"  Next: '{lines[i+1]}'")
                trans_found += 1
                if trans_found >= 3:
                    break