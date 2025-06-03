"""
Enhanced validator for PDF transaction extraction accuracy

This module provides comprehensive validation of extracted transaction data,
including confidence scoring and potential missed transaction detection.
"""

import os
import pdfplumber
import pandas as pd
from datetime import datetime
import re

from config import (
    CONFIDENCE_EXCELLENT,          # 95
    CONFIDENCE_GOOD,              # 85
    MAX_EXTRACTION_PENALTY,       # 50
    MAX_MISSED_PENALTY,           # 30
    MAX_AMOUNT_PENALTY,           # 25
    MISSED_TRANSACTION_PENALTY    # 5
)


class TransactionValidator:
    """Enhanced validator for PDF transaction extraction accuracy"""
    
    def __init__(self):
        self.validation_results = {}
        self.potential_missed = []
        
    def validate_extraction(self, pdf_path, extracted_data, statement_type):
        """Main validation method that runs all checks"""
        print(f"\n🔍 VALIDATING: {os.path.basename(pdf_path)}")
        
        validation_result = {
            'pdf_file': os.path.basename(pdf_path),
            'statement_type': statement_type,
            'extracted_count': len(extracted_data),
            'potential_missed': [],
            'amount_discrepancy': None,
            'confidence_score': 0
        }
        
        # Method 1: Count potential transaction lines in raw text
        raw_count = self.count_potential_transactions_in_text(pdf_path, statement_type)
        validation_result['estimated_total'] = raw_count
        
        # Method 2: Check for amount discrepancies
        amount_check = self.validate_amounts(pdf_path, extracted_data, statement_type)
        validation_result['amount_discrepancy'] = amount_check
        
        # Method 3: Find potential missed transactions
        missed_transactions = self.find_potential_missed_transactions(pdf_path, extracted_data, statement_type)
        validation_result['potential_missed'] = missed_transactions
        
        # Method 4: Calculate confidence score
        validation_result['confidence_score'] = self.calculate_confidence_score(validation_result)
        
        # Method 5: Generate validation report
        self.print_validation_report(validation_result)
        
        return validation_result
    
    def count_potential_transactions_in_text(self, pdf_path, statement_type):
        """Count lines that look like transactions in the raw PDF text"""
        transaction_count = 0
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    try:
                        text = page.extract_text()
                        if not text:
                            continue
                            
                        lines = text.split('\n')
                        for line in lines:
                            line = line.strip()
                            
                            # Skip obvious non-transaction lines
                            if (len(line) < 10 or 
                                'Merchant Name' in line or
                                'Date of' in line or
                                'Transaction' in line or
                                'ACCOUNT ACTIVITY' in line or
                                'Page' in line or
                                'Statement' in line or
                                line.startswith('This Statement') or
                                line.startswith('CHASE') or
                                line.startswith('AMERICAN EXPRESS')):
                                continue
                            
                            # Check if line looks like a transaction
                            if statement_type == 'amex':
                                if self.looks_like_amex_transaction(line):
                                    transaction_count += 1
                            elif statement_type == 'chase':
                                if self.looks_like_chase_transaction(line):
                                    transaction_count += 1
                    except Exception:
                        continue
        except Exception as e:
            print(f"❌ Error counting transactions: {e}")
            
        return transaction_count
    
    def looks_like_amex_transaction(self, line):
        """Check if a line looks like an AmEx transaction"""
        # Pattern: Date + text + amount
        date_pattern = r'^\d{1,2}/\d{1,2}(?:/\d{2,4})?'
        amount_pattern = r'[-]?\$?[\d,]+\.\d{2}$'
        
        return (re.search(date_pattern, line) and 
                re.search(amount_pattern, line) and
                len(line.split()) >= 3)
    
    def looks_like_chase_transaction(self, line):
        """Check if a line looks like a Chase transaction"""
        # Pattern: MM/DD + text + amount
        pattern = r'^\d{1,2}/\d{1,2}\s*(&?).*\d{1,3}(?:,\d{3})*\.\d{2}$'
        return re.match(pattern, line) is not None
    
    def validate_amounts(self, pdf_path, extracted_data, statement_type):
        """Look for total amount discrepancies"""
        try:
            # Calculate sum of extracted transactions
            extracted_total = sum(float(t['Amount'].replace(',', '')) for t in extracted_data)
            
            # Look for statement totals in PDF
            statement_totals = self.find_statement_totals(pdf_path, statement_type)
            
            if statement_totals:
                for total_type, amount in statement_totals.items():
                    difference = abs(extracted_total - amount)
                    if difference > 0.01:  # Allow for small rounding differences
                        return {
                            'extracted_total': extracted_total,
                            'statement_total': amount,
                            'total_type': total_type,
                            'difference': difference
                        }
            
            return None
            
        except Exception as e:
            print(f"❌ Error validating amounts: {e}")
            return None
    
    def find_statement_totals(self, pdf_path, statement_type):
        """Extract total amounts from PDF (New Charges, etc.)"""
        totals = {}
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_text = ""
                for page in pdf.pages:
                    try:
                        text = page.extract_text()
                        if text:
                            full_text += text + "\n"
                    except Exception:
                        continue
                
                # Look for common total patterns
                if statement_type == 'amex':
                    # AmEx patterns
                    patterns = {
                        'new_charges': r'New Charges.*?\$?([\d,]+\.\d{2})',
                        'total_charges': r'Total.*?Charges.*?\$?([\d,]+\.\d{2})',
                        'purchases': r'Purchases.*?\$?([\d,]+\.\d{2})'
                    }
                elif statement_type == 'chase':
                    # Chase patterns
                    patterns = {
                        'purchases': r'Purchases.*?\$?([\d,]+\.\d{2})',
                        'new_charges': r'New Charges.*?\$?([\d,]+\.\d{2})',
                        'total_activity': r'Total.*?Activity.*?\$?([\d,]+\.\d{2})'
                    }
                
                for total_type, pattern in patterns.items():
                    matches = re.findall(pattern, full_text, re.IGNORECASE)
                    if matches:
                        try:
                            amount = float(matches[0].replace(',', ''))
                            totals[total_type] = amount
                        except ValueError:
                            continue
                            
        except Exception as e:
            print(f"❌ Error finding statement totals: {e}")
            
        return totals
    
    def find_potential_missed_transactions(self, pdf_path, extracted_data, statement_type):
        """Find lines that look like transactions but weren't extracted"""
        potential_missed = []
        extracted_lines = set()
        
        # Create a set of extracted transaction signatures
        for transaction in extracted_data:
            signature = f"{transaction['Date']}|{transaction['Merchant'][:20]}|{transaction['Amount']}"
            extracted_lines.add(signature)
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        text = page.extract_text()
                        if not text:
                            continue
                            
                        lines = text.split('\n')
                        for line_num, line in enumerate(lines, 1):
                            line = line.strip()
                            
                            # Check if this looks like a transaction
                            if statement_type == 'amex' and self.looks_like_amex_transaction(line):
                                parsed = self.quick_parse_amex_line(line)
                                if parsed:
                                    signature = f"{parsed['date']}|{parsed['merchant'][:20]}|{parsed['amount']}"
                                    if signature not in extracted_lines:
                                        potential_missed.append({
                                            'page': page_num,
                                            'line': line_num,
                                            'text': line,
                                            'parsed': parsed
                                        })
                            
                            elif statement_type == 'chase' and self.looks_like_chase_transaction(line):
                                parsed = self.quick_parse_chase_line(line)
                                if parsed:
                                    signature = f"{parsed['date']}|{parsed['merchant'][:20]}|{parsed['amount']}"
                                    if signature not in extracted_lines:
                                        potential_missed.append({
                                            'page': page_num,
                                            'line': line_num,
                                            'text': line,
                                            'parsed': parsed
                                        })
                    except Exception:
                        continue
        except Exception as e:
            print(f"❌ Error finding missed transactions: {e}")
            
        return potential_missed
    
    def quick_parse_amex_line(self, line):
        """Quickly parse an AmEx line to extract basic info"""
        try:
            date_match = re.match(r'^(\d{1,2}/\d{1,2}(?:/\d{2,4})?)', line)
            amount_match = re.search(r'([-]?\$?[\d,]+\.\d{2})$', line)
            
            if date_match and amount_match:
                date_part = date_match.group(1)
                amount_str = amount_match.group(1).replace('$', '').replace(',', '')
                
                # Skip negative amounts
                try:
                    if float(amount_str) <= 0:
                        return None
                except ValueError:
                    return None
                
                # Extract merchant (simplified)
                start = date_match.end()
                end = amount_match.start()
                merchant = line[start:end].strip()
                
                return {
                    'date': date_part,
                    'merchant': merchant,
                    'amount': amount_str
                }
        except Exception:
            pass
        return None
    
    def quick_parse_chase_line(self, line):
        """Quickly parse a Chase line to extract basic info"""
        try:
            pattern = r'^(\d{1,2}/\d{1,2})\s*(&?)\s*(.+?)\s+([-]?\d{1,3}(?:,\d{3})*\.\d{2})$'
            match = re.match(pattern, line)
            
            if match:
                date = match.group(1)
                merchant = match.group(3).strip()
                amount = match.group(4)
                
                # Skip negative amounts
                try:
                    if float(amount) <= 0:
                        return None
                except ValueError:
                    return None
                
                return {
                    'date': date,
                    'merchant': merchant,
                    'amount': amount
                }
        except Exception:
            pass
        return None
    
    def calculate_confidence_score(self, validation_result):
        """Calculate a confidence score (0-100) for the extraction"""
        score = 100
        
        extracted = validation_result['extracted_count']
        estimated = validation_result['estimated_total']
        missed = len(validation_result['potential_missed'])
        
        # Penalize based on extraction ratio
        if estimated > 0:
            extraction_ratio = extracted / estimated
            if extraction_ratio < 0.95:
                score -= (1 - extraction_ratio) * MAX_EXTRACTION_PENALTY
        
        # Penalize for potential missed transactions
        if missed > 0:
            penalty = min(missed * MISSED_TRANSACTION_PENALTY, MAX_MISSED_PENALTY)
            score -= penalty
        
        # Penalize for amount discrepancies
        if validation_result['amount_discrepancy']:
            diff_percent = (validation_result['amount_discrepancy']['difference'] / 
                          validation_result['amount_discrepancy']['extracted_total']) * 100
            penalty = min(diff_percent * 2, MAX_AMOUNT_PENALTY)
            score -= penalty
        
        return max(0, int(score))
    
    def print_validation_report(self, result):
        """Print a detailed validation report"""
        print(f"\n📊 VALIDATION REPORT for {result['pdf_file']}")
        print("=" * 60)
        
        print(f"📄 Statement Type: {result['statement_type'].upper()}")
        print(f"✅ Extracted Transactions: {result['extracted_count']}")
        print(f"🔢 Estimated Total in PDF: {result['estimated_total']}")
        
        if result['extracted_count'] != result['estimated_total']:
            diff = result['estimated_total'] - result['extracted_count']
            print(f"⚠️  Potential Missing: {diff} transactions")
        else:
            print(f"✅ Perfect match!")
        
        # Amount validation
        if result['amount_discrepancy']:
            disc = result['amount_discrepancy']
            print(f"\n💰 AMOUNT VALIDATION:")
            print(f"   Extracted Total: ${disc['extracted_total']:,.2f}")
            print(f"   Statement {disc['total_type']}: ${disc['statement_total']:,.2f}")
            print(f"   Difference: ${disc['difference']:,.2f}")
        else:
            print(f"💰 Amount Validation: ✅ No discrepancies found")
        
        # Potential missed transactions
        if result['potential_missed']:
            print(f"\n🚨 POTENTIAL MISSED TRANSACTIONS ({len(result['potential_missed'])}):")
            for i, missed in enumerate(result['potential_missed'][:5], 1):  # Show first 5
                print(f"   {i}. Page {missed['page']}: {missed['text'][:80]}...")
            
            if len(result['potential_missed']) > 5:
                print(f"   ... and {len(result['potential_missed']) - 5} more")
        else:
            print(f"🚨 Potential Missed: ✅ None found")
        
        # Confidence score
        score = result['confidence_score']
        if score >= CONFIDENCE_EXCELLENT:
            emoji = "🟢"
            status = "EXCELLENT"
        elif score >= CONFIDENCE_GOOD:
            emoji = "🟡"
            status = "GOOD"
        else:
            emoji = "🔴"
            status = "NEEDS REVIEW"
        
        print(f"\n{emoji} CONFIDENCE SCORE: {score}% ({status})")
        print("=" * 60)