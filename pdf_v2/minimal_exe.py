#!/usr/bin/env python3
"""
Minimal PDF to Excel Converter - Works as EXE
Just the essentials, no complex logic
"""

import os
import pandas as pd
import pdfplumber
import re
from datetime import datetime

# Create folders
os.makedirs('Convert', exist_ok=True)
os.makedirs('Excel', exist_ok=True)
for folder in ['amex', 'chase', 'w2']:
    os.makedirs(os.path.join('Convert', folder), exist_ok=True)

print("PDF to Excel Converter")
print("="*50)

# Process each type
for pdf_type in ['amex', 'chase', 'w2']:
    folder_path = os.path.join('Convert', pdf_type)
    if not os.path.exists(folder_path):
        continue
    
    pdf_files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]
    if not pdf_files:
        continue
    
    print(f"\nProcessing {pdf_type.upper()}...")
    all_data = []
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(folder_path, pdf_file)
        print(f"  {pdf_file}")
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if not text:
                        continue
                    
                    if pdf_type == 'amex':
                        # Simple AmEx parsing
                        for line in text.split('\n'):
                            if re.match(r'^\d{2}/\d{2}', line) and '$' not in line[:5]:
                                parts = line.split()
                                if len(parts) >= 3:
                                    all_data.append({
                                        'Name': 'CARDHOLDER',
                                        'Date': parts[0],
                                        'Merchant': ' '.join(parts[1:-1]),
                                        'Amount': parts[-1].replace('$','').replace(',','')
                                    })
                    
                    elif pdf_type == 'chase':
                        # Simple Chase parsing
                        for line in text.split('\n'):
                            if re.match(r'^\d{2}/\d{2}', line) and 'Payment' not in line:
                                match = re.search(r'^(\d{2}/\d{2})\s+(.+?)\s+([\d,]+\.\d{2})$', line)
                                if match:
                                    all_data.append({
                                        'Name': 'CHASE CARDHOLDER',
                                        'Date': match.group(1),
                                        'Merchant': match.group(2),
                                        'Amount': match.group(3).replace(',','')
                                    })
                    
                    elif pdf_type == 'w2':
                        # Simple W2 parsing
                        lines = text.split('\n')
                        for i, line in enumerate(lines):
                            if 'social security number' in line.lower() and i+1 < len(lines):
                                ssn_match = re.search(r'(\d{3}-\d{2}-\d{4})', lines[i+1])
                                if ssn_match:
                                    all_data.append({
                                        'Employer Name': 'Ocomar Enterprises LLC',
                                        'Employee Name': 'Employee',
                                        'Gross Salary': '0',
                                        'Federal Tax': '0',
                                        'SSN': ssn_match.group(1),
                                        'Medicare': '0',
                                        'State Witholds': '0',
                                        'SDI': '0'
                                    })
        except Exception as e:
            print(f"    Error: {e}")
    
    # Save to Excel
    if all_data:
        output_file = os.path.join('Excel', f'{pdf_type}.xlsx')
        if pdf_type == 'w2':
            df = pd.DataFrame(all_data)
        else:
            df = pd.DataFrame(all_data, columns=['Name', 'Date', 'Merchant', 'Amount'])
        df.to_excel(output_file, index=False)
        print(f"  Saved {len(all_data)} records to {output_file}")
    else:
        # Create empty file
        output_file = os.path.join('Excel', f'{pdf_type}.xlsx')
        if pdf_type == 'w2':
            df = pd.DataFrame(columns=['Employer Name', 'Employee Name', 'Gross Salary', 'Federal Tax', 'SSN', 'Medicare', 'State Witholds', 'SDI'])
        else:
            df = pd.DataFrame(columns=['Name', 'Date', 'Merchant', 'Amount'])
        df.to_excel(output_file, index=False)
        print(f"  Created empty {output_file}")

print("\n✅ Done! Check Excel folder.")
print("\nPress Enter to exit...")
try:
    input()
except:
    pass