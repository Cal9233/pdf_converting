import os
import pdfplumber
import pandas as pd
from datetime import datetime
import re
import time
import sys
import threading

# class TransactionValidator:
#     """Enhanced validator for PDF transaction extraction accuracy"""
    
#     def __init__(self):
#         self.validation_results = {}
#         self.potential_missed = []
        
#     def validate_extraction(self, pdf_path, extracted_data, statement_type):
#         """Main validation method that runs all checks"""
#         print(f"\n🔍 VALIDATING: {os.path.basename(pdf_path)}")
        
#         validation_result = {
#             'pdf_file': os.path.basename(pdf_path),
#             'statement_type': statement_type,
#             'extracted_count': len(extracted_data),
#             'potential_missed': [],
#             'amount_discrepancy': None,
#             'confidence_score': 0
#         }
        
#         # Method 1: Count potential transaction lines in raw text
#         raw_count = self.count_potential_transactions_in_text(pdf_path, statement_type)
#         validation_result['estimated_total'] = raw_count
        
#         # Method 2: Check for amount discrepancies
#         amount_check = self.validate_amounts(pdf_path, extracted_data, statement_type)
#         validation_result['amount_discrepancy'] = amount_check
        
#         # Method 3: Find potential missed transactions
#         missed_transactions = self.find_potential_missed_transactions(pdf_path, extracted_data, statement_type)
#         validation_result['potential_missed'] = missed_transactions
        
#         # Method 4: Calculate confidence score
#         validation_result['confidence_score'] = self.calculate_confidence_score(validation_result)
        
#         # Method 5: Generate validation report
#         self.print_validation_report(validation_result)
        
#         return validation_result
    
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
                score -= (1 - extraction_ratio) * 50
        
        # Penalize for potential missed transactions
        if missed > 0:
            penalty = min(missed * 5, 30)  # Max 30 point penalty
            score -= penalty
        
        # Penalize for amount discrepancies
        if validation_result['amount_discrepancy']:
            diff_percent = (validation_result['amount_discrepancy']['difference'] / 
                          validation_result['amount_discrepancy']['extracted_total']) * 100
            penalty = min(diff_percent * 2, 25)  # Max 25 point penalty
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
        if score >= 95:
            emoji = "🟢"
            status = "EXCELLENT"
        elif score >= 85:
            emoji = "🟡"
            status = "GOOD"
        else:
            emoji = "🔴"
            status = "NEEDS REVIEW"
        
        print(f"\n{emoji} CONFIDENCE SCORE: {score}% ({status})")
        print("=" * 60)

class UniversalPDFToExcelConverter:
    def __init__(self):
        self.convert_folder = "Convert"
        self.excel_folder = "Excel"
        self.chase_date_range = None
        self.progress_window = None
        self.validator = TransactionValidator()
        
    def show_progress_window(self):
        """Show a clean progress window to indicate the program is running"""
        try:
            import tkinter as tk
            from tkinter import ttk
            
            self.progress_window = tk.Tk()
            self.progress_window.title("PDF to Excel Converter")
            self.progress_window.geometry("350x150")
            self.progress_window.resizable(False, False)
            
            # Center the window
            self.progress_window.eval('tk::PlaceWindow . center')
            
            # Main frame
            main_frame = tk.Frame(self.progress_window, padx=20, pady=20)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Title
            title_label = tk.Label(main_frame, text="🏦 PDF to Excel Converter", 
                                 font=("Arial", 14, "bold"))
            title_label.pack(pady=(0, 15))
            
            # Status label
            self.status_label = tk.Label(main_frame, text="🚀 Starting conversion process...", 
                                       font=("Arial", 10))
            self.status_label.pack(pady=(0, 15))
            
            # Progress bar
            self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
            self.progress_bar.pack(fill=tk.X, pady=(0, 15))
            self.progress_bar.start(10)
            
            # Current file label
            self.file_label = tk.Label(main_frame, text="", 
                                     font=("Arial", 9), fg="gray")
            self.file_label.pack()
            
            # Don't allow closing
            self.progress_window.protocol("WM_DELETE_WINDOW", lambda: None)
            
            return self.progress_window
            
        except Exception:
            return None
    
    def update_progress(self, status_text, file_text="", force_update=False):
        """Update the progress window with current status (simplified)"""
        try:
            if self.progress_window and (force_update or time.time() - getattr(self, '_last_update', 0) > 0.3):
                self.status_label.config(text=status_text)
                if file_text:
                    self.file_label.config(text=file_text)
                self.progress_window.update_idletasks()
                self._last_update = time.time()
        except Exception:
            # Fallback to console only for critical updates
            if force_update:
                print(status_text)
    
    def close_progress_window(self):
        """Close the progress window"""
        try:
            if self.progress_window:
                self.progress_bar.stop()
                self.progress_window.destroy()
                self.progress_window = None
        except Exception:
            pass
        
    # def setup_folders(self):
    #     """Create the Convert and Excel folders if they don't exist"""
    #     try:
    #         if not os.path.exists(self.convert_folder):
    #             os.makedirs(self.convert_folder)
    #             self.update_progress("📁 Created Convert folder", f"Created '{self.convert_folder}' folder")
                
    #         if not os.path.exists(self.excel_folder):
    #             os.makedirs(self.excel_folder)
    #             self.update_progress("📁 Created Excel folder", f"Created '{self.excel_folder}' folder")
    #     except Exception as e:
    #         self.update_progress("⚠️ Folder creation warning", f"Could not create folders: {str(e)}")
    
    def extract_chase_date_range(self, text):
        """Extract the date range from Chase PDF ACCOUNT SUMMARY section"""
        try:
            lines = text.split('\n')
            
            for i, line in enumerate(lines):
                # Look for "Opening/Closing Date" or similar patterns
                if ('Opening/Closing Date' in line or 
                    'OPENING/CLOSING DATE' in line.upper()):
                    
                    # The date range might be on the same line or the next line
                    date_line = line
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if re.search(r'\d{2}/\d{2}/\d{2}', next_line):
                            date_line = next_line
                    
                    # Extract date range pattern: MM/DD/YY - MM/DD/YY
                    date_pattern = r'^(\d{1,2}/\d{1,2})\s*(&?)\s*(.+?)\s+([-]?\d{1,}(?:,\d{3})*\.\d{2})$'
                    match = re.search(date_pattern, date_line)
                    
                    if match:
                        start_date = match.group(1)
                        end_date = match.group(2)
                        
                        # Convert to full format
                        start_full = self.convert_chase_date_to_full(start_date)
                        end_full = self.convert_chase_date_to_full(end_date)
                        
                        self.update_progress("📅 Found Chase date range", 
                                           f"Date range: {start_full} to {end_full}", force_update=True)
                        
                        return {
                            'start': start_full,
                            'end': end_full,
                            'start_month': int(start_full.split('/')[0]),
                            'end_month': int(end_full.split('/')[0]),
                            'start_year': int(start_full.split('/')[2]),
                            'end_year': int(end_full.split('/')[2])
                        }
            
            # Fallback: try to find any date pattern in ACCOUNT SUMMARY section
            account_summary_section = ""
            in_summary = False
            
            for line in lines:
                if 'ACCOUNT SUMMARY' in line.upper():
                    in_summary = True
                    continue
                elif in_summary and (line.strip() == "" or 
                                   'YOUR ACCOUNT MESSAGES' in line.upper() or
                                   'ACCOUNT ACTIVITY' in line.upper()):
                    break
                elif in_summary:
                    account_summary_section += line + "\n"
            
            # Look for any date range in the summary section
            date_pattern = r'(\d{1,2}/\d{1,2}/\d{2,4})\s*-\s*(\d{1,2}/\d{1,2}/\d{2,4})'
            match = re.search(date_pattern, date_line)

            if match:
                start_date = match.group(1)
                end_date = match.group(2)
                
                start_full = self.convert_chase_date_to_full(start_date)
                end_full = self.convert_chase_date_to_full(end_date)
                
                self.update_progress("📅 Found Chase date range (fallback)", 
                                   f"Date range: {start_full} to {end_full}", force_update=True)
                
                return {
                    'start': start_full,
                    'end': end_full,
                    'start_month': int(start_full.split('/')[0]),
                    'end_month': int(end_full.split('/')[0]),
                    'start_year': int(start_full.split('/')[2]),
                    'end_year': int(end_full.split('/')[2])
                }
            
        except Exception as e:
            self.update_progress("⚠️ Date extraction warning", f"Could not extract Chase date range", force_update=True)
        
        return None
    
    # def convert_chase_date_to_full(self, date_str):
    #     """Convert MM/DD/YY to MM/DD/YYYY"""
    #     try:
    #         parts = date_str.split('/')
    #         if len(parts) == 3:
    #             month, day, year = parts
    #             if len(year) == 2:
    #                 year_num = int(year)
    #                 if year_num >= 50:
    #                     full_year = f"19{year_num}"
    #                 else:
    #                     full_year = f"20{year_num}"
    #                 return f"{month}/{day}/{full_year}"
    #             else:
    #                 return date_str
    #     except Exception:
    #         pass
    #     return date_str
    
    # def get_chase_transaction_year(self, transaction_month):
    #     """Determine the correct year for a Chase transaction based on the date range"""
    #     try:
    #         if not self.chase_date_range:
    #             # Fallback to current year
    #             return datetime.now().year
            
    #         start_month = self.chase_date_range['start_month']
    #         end_month = self.chase_date_range['end_month']
    #         start_year = self.chase_date_range['start_year']
    #         end_year = self.chase_date_range['end_year']
            
    #         # Handle year boundary cases (e.g., 12/24/24 - 01/23/25)
    #         if start_year != end_year:
    #             if transaction_month >= start_month:
    #                 return start_year
    #             else:
    #                 return end_year
    #         else:
    #             # Same year for all transactions
    #             return start_year
                
    #     except Exception:
    #         return datetime.now().year
            
    # def detect_statement_type(self, text, filename):
    #     """Detect if the PDF is American Express or Chase"""
    #     try:
    #         text_upper = text.upper()
    #         filename_upper = filename.upper()
            
    #         # Check filename first for more reliable detection
    #         if 'AMEX' in filename_upper or 'AMERICAN' in filename_upper:
    #             return 'amex'
    #         elif 'CHASE' in filename_upper:
    #             return 'chase'
            
    #         # Fallback to content detection
    #         if 'AMERICAN EXPRESS' in text_upper or 'AMAZON BUSINESS PRIME CARD' in text_upper:
    #             return 'amex'
    #         elif 'CHASE' in text_upper and ('ULTIMATE REWARDS' in text_upper or 'ACCOUNT ACTIVITY' in text_upper):
    #             return 'chase'
    #         else:
    #             return 'unknown'
    #     except Exception:
    #         return 'unknown'
    
    def extract_pdf_content(self, pdf_path):
        """Extract transaction data and validate results"""
        extracted_data = []
        statement_type = 'unknown'
        
        # GLOBAL: Track cardholder across the ENTIRE document
        self.global_current_cardholder = "Unknown"
        
        self.update_progress("📄 Reading PDF content...", f"Processing: {os.path.basename(pdf_path)}", force_update=True)
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Get full text for detection and date extraction
                full_text = ""
                for page in pdf.pages:
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            full_text += page_text + "\n"
                    except Exception:
                        continue
                
                filename = os.path.basename(pdf_path)
                statement_type = self.detect_statement_type(full_text, filename)
                self.update_progress(f"🔍 Detected: {statement_type}", "", force_update=True)
                
                # Extract date range for Chase statements
                if statement_type == 'chase':
                    self.chase_date_range = self.extract_chase_date_range(full_text)
                
                # Extract transactions from all pages
                self.update_progress(f"📖 Processing {len(pdf.pages)} pages...", "", force_update=True)
                
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            if page_num % 5 == 1 or page_num == len(pdf.pages):
                                self.update_progress(f"📄 Processing page {page_num}...", "", force_update=True)
                            
                            if statement_type == 'amex':
                                # Use the AmEx global parser if it exists, otherwise use regular
                                if hasattr(self, 'parse_amex_page_global'):
                                    page_transactions = self.parse_amex_page_global(page_text, page_num)
                                else:
                                    page_transactions = self.parse_amex_page(page_text, page_num)
                            elif statement_type == 'chase':
                                # Use the updated Chase parser
                                page_transactions = self.parse_chase_page(page_text, page_num)
                            else:
                                continue
                            
                            extracted_data.extend(page_transactions)
                    except Exception as e:
                        continue
                
                # VALIDATION STEP - Add this after extraction
                if extracted_data and statement_type != 'unknown':
                    self.update_progress("🔍 Validating extraction...", "Checking for missed transactions", force_update=True)
                    validation_result = self.validator.validate_extraction(pdf_path, extracted_data, statement_type)
                    
                    # Store validation results for later reporting
                    self.validator.validation_results[pdf_path] = validation_result
        
        except Exception as e:
            self.update_progress("❌ PDF processing error", f"Error: {str(e)}")
            return None, statement_type
            
        return extracted_data, statement_type
    
    # def create_validation_report(self):
    #     """Create a comprehensive validation report"""
    #     report_path = os.path.join(self.excel_folder, f"Validation_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        
    #     try:
    #         with open(report_path, 'w') as f:
    #             f.write("PDF TO EXCEL CONVERSION - VALIDATION REPORT\n")
    #             f.write("=" * 50 + "\n\n")
    #             f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
    #             for pdf_path, result in self.validator.validation_results.items():
    #                 f.write(f"FILE: {result['pdf_file']}\n")
    #                 f.write("-" * 30 + "\n")
    #                 f.write(f"Statement Type: {result['statement_type'].upper()}\n")
    #                 f.write(f"Extracted: {result['extracted_count']} transactions\n")
    #                 f.write(f"Estimated Total: {result['estimated_total']} transactions\n")
    #                 f.write(f"Confidence Score: {result['confidence_score']}%\n")
                    
    #                 if result['amount_discrepancy']:
    #                     disc = result['amount_discrepancy']
    #                     f.write(f"Amount Discrepancy: ${disc['difference']:,.2f}\n")
                    
    #                 if result['potential_missed']:
    #                     f.write(f"Potential Missed: {len(result['potential_missed'])} transactions\n")
    #                     f.write("Details:\n")
    #                     for missed in result['potential_missed']:
    #                         f.write(f"  Page {missed['page']}: {missed['text']}\n")
                    
    #                 f.write("\n")
                
    #         print(f"\n📋 Validation report saved: {report_path}")
            
    #     except Exception as e:
    #         print(f"❌ Error creating validation report: {e}")
    
    # def parse_amex_page(self, page_text, page_num):
    #     """Parse American Express transactions from a single page"""
    #     transactions = []
        
    #     try:
    #         lines = page_text.split('\n')
            
    #         for i, line in enumerate(lines):
    #             try:
    #                 line = line.strip()
                    
    #                 # Skip empty lines and headers
    #                 if (len(line) < 8 or
    #                     'Merchant Name' in line or
    #                     '$ Amount' in line or
    #                     'Date of' in line or
    #                     line.startswith('Transaction') or
    #                     line.startswith('Amazon Business') or
    #                     line.startswith('AMERICAN EXPRESS') or
    #                     line.startswith('Account Ending') or
    #                     line.startswith('Page') or
    #                     line.startswith('Customer Care')):
    #                     continue
                    
    #                 # Try to parse as transaction
    #                 transaction = self.parse_amex_transaction_line(line)
    #                 if transaction:
    #                     transactions.append(transaction)
                
    #             except Exception:
    #                 continue
        
    #     except Exception:
    #         pass
        
    #     return transactions
    
    # def parse_amex_transaction_line(self, line):
    #     """Parse individual American Express transaction line"""
    #     try:
    #         # Step 1: Extract date (MM/DD or MM/DD/YY) from the beginning
    #         date_match = re.match(r'^(\d{1,2}/\d{1,2}(?:/\d{2,4})?)', line)
    #         if not date_match:
    #             return None
            
    #         date_part = date_match.group(1)
    #         remaining_text = line[date_match.end():].strip()
            
    #         # Step 2: Extract amount from the end (look for $XX.XX pattern)
    #         amount_match = re.search(r'([-]?\$?[\d,]+\.\d{2})$', remaining_text)
    #         if not amount_match:
    #             return None
            
    #         amount_str = amount_match.group(1)
    #         merchant_and_location = remaining_text[:amount_match.start()].strip()
            
    #         # Step 3: Clean up amount and check if it's a charge (positive)
    #         amount_str = amount_str.replace('$', '').replace(',', '')
            
    #         # Skip negative amounts (payments/credits)
    #         try:
    #             amount_value = float(amount_str)
    #             if amount_value <= 0:
    #                 return None  # Skip payments and credits
    #         except ValueError:
    #             return None  # Skip if amount can't be parsed
            
    #         # Step 4: Extract ONLY merchant name from the middle part
    #         merchant_name = self.extract_merchant_name(merchant_and_location)
            
    #         if not merchant_name or len(merchant_name) < 3:
    #             return None
            
    #         # Step 5: Handle date conversion
    #         full_date = self.convert_date(date_part)
    #         if not full_date:
    #             return None
            
    #         return {
    #             'Date': full_date,
    #             'Merchant': merchant_name,
    #             'Amount': amount_str
    #         }
        
    #     except Exception:
    #         return None
    
    # def extract_merchant_name(self, text):
    #     """Extract only the merchant name, excluding location and personal info"""
    #     try:
    #         # Remove common prefixes
    #         text = re.sub(r'^(AplPay|TST\*|SQ \*)', '', text).strip()
            
    #         # Split by common delimiters and patterns
    #         words = text.split()
    #         merchant_parts = []
            
    #         for word in words:
    #             # Stop at common location indicators
    #             if (word.upper() in ['CA', 'NY', 'TX', 'FL', 'WA', 'OR', 'NV', 'AZ'] or  # State codes
    #                 re.match(r'^\d{3}-\d{3}-\d{4}$', word) or  # Phone numbers
    #                 re.match(r'^\d{10,}$', word) or  # Long numbers
    #                 word.lower().endswith('.com') or  # Websites
    #                 word.lower().endswith('.net') or
    #                 word.lower().endswith('.org') or
    #                 len(word) > 20):  # Very long words (likely IDs or URLs)
    #                 break
                
    #             # Add word to merchant name if it looks valid
    #             if (len(word) >= 2 and 
    #                 not word.isdigit() and 
    #                 word.upper() not in ['AND', 'THE', 'OF', 'IN', 'AT', 'FOR']):
    #                 merchant_parts.append(word)
            
    #         # Join the merchant parts
    #         merchant_name = ' '.join(merchant_parts)
            
    #         # Clean up common patterns
    #         merchant_name = re.sub(r'\s+', ' ', merchant_name)  # Multiple spaces
    #         merchant_name = re.sub(r'[#*]+.*$', '', merchant_name)  # Remove # and * suffixes
    #         merchant_name = merchant_name.strip()
            
    #         # Additional cleanup for specific patterns
    #         merchant_name = re.sub(r'\s+\d{3,}$', '', merchant_name)
            
    #         return merchant_name
        
    #     except Exception:
    #         return ""
    
    # def convert_date(self, date_str):
    #     """Convert date string to full format"""
    #     try:
    #         if '/' in date_str:
    #             date_components = date_str.split('/')
    #             if len(date_components) == 3:
    #                 # Full date with year (MM/DD/YY)
    #                 month, day, year = date_components
    #                 if len(year) == 2:
    #                     # Convert 2-digit year to 4-digit year
    #                     year_num = int(year)
    #                     if year_num >= 50:  # Assume 1950-1999
    #                         full_year = f"19{year_num}"
    #                     else:  # Assume 2000-2049
    #                         full_year = f"20{year_num}"
    #                     return f"{month}/{day}/{full_year}"
    #                 else:
    #                     return date_str
    #             elif len(date_components) == 2:
    #                 # MM/DD format - use current year
    #                 current_year = datetime.now().year
    #                 return f"{date_str}/{current_year}"
    #     except Exception:
    #         pass
        
    #     return None
    
    def parse_chase_page(self, page_text, page_num):
        """Parse Chase page with enhanced name detection and debugging"""
        transactions = []
        
        print(f"\n📄 DEBUG: Starting Chase page {page_num} with global cardholder: '{getattr(self, 'global_current_cardholder', 'Unknown')}'")
        
        # Initialize global cardholder if not exists
        if not hasattr(self, 'global_current_cardholder'):
            self.global_current_cardholder = "Unknown"
        
        try:
            lines = page_text.split('\n')
            print(f"📄 DEBUG: Chase page {page_num} has {len(lines)} lines")
            
            # CHASE STRATEGY: Parse all transactions first, then assign names retroactively
            temp_transactions = []  # Store transactions without names first
            page_cardholders_found = []  # Track all cardholders found on this page
            
            for i, line in enumerate(lines):
                try:
                    line = line.strip()
                    
                    # Skip empty lines
                    if len(line) < 5:
                        continue
                    
                    # Skip headers
                    if (('Date of' in line and 'Transaction' in line) or
                        'Merchant Name' in line or
                        'ACCOUNT ACTIVITY' in line or
                        line.startswith('CHASE') or
                        line.startswith('Page') or
                        line.startswith('Customer Service')):
                        continue
                    
                    # Enhanced Chase name detection
                    cardholder_name = self.extract_chase_cardholder_name(line, lines, i)
                    if cardholder_name:
                        page_cardholders_found.append(cardholder_name)
                        print(f"🏷️  DEBUG: CHASE CARDHOLDER FOUND on line {i+1}: '{cardholder_name}'")
                        
                        # Count how many Unknown transactions we're about to assign
                        unknown_count = sum(1 for t in temp_transactions if t.get('Name') == 'Unknown')
                        print(f"   📊 Will assign '{cardholder_name}' to {unknown_count} Unknown transactions")
                        
                        # Assign this name to all previous temp_transactions that are Unknown
                        assigned_count = 0
                        for temp_trans in temp_transactions:
                            if temp_trans.get('Name') == 'Unknown':
                                temp_trans['Name'] = cardholder_name
                                assigned_count += 1
                                if assigned_count <= 3:  # Show first 3 assignments
                                    print(f"   🔄 ASSIGNED: '{cardholder_name}' to {temp_trans['Date']} {temp_trans['Merchant'][:20]}...")
                                elif assigned_count == 4:
                                    print(f"   🔄 ... and {unknown_count - 3} more transactions")
                        
                        # Update global cardholder for future transactions
                        self.global_current_cardholder = cardholder_name
                        print(f"   🌐 Updated global cardholder to: '{cardholder_name}'")
                        continue
                    
                    # Try to parse as transaction
                    transaction = self.parse_chase_transaction_line(line)
                    if transaction:
                        # For Chase, start with Unknown and assign name later
                        transaction['Name'] = 'Unknown'
                        temp_transactions.append(transaction)
                        if len(temp_transactions) % 10 == 1:  # Show every 10th transaction to avoid spam
                            print(f"💳 DEBUG: Chase transaction #{len(temp_transactions)} on line {i+1} (pending name assignment)")
                            print(f"   TRANSACTION: {transaction['Date']} | {transaction['Merchant'][:30]}... | ${transaction['Amount']}")
                    else:
                        # Enhanced debugging for potential missed transactions
                        if (len(line) > 15 and 
                            any(char.isdigit() for char in line) and 
                            ('$' in line or re.search(r'\d+\.\d{2}', line)) and
                            not any(skip in line.upper() for skip in ['TOTAL', 'BALANCE', 'PAYMENT', 'CREDIT', 'AUTOPAY', 'MINIMUM'])):
                            # Only show first few potential missed transactions to avoid spam
                            missed_shown = sum(1 for t in temp_transactions if 'potential_missed' in str(t))
                            if missed_shown < 3:
                                print(f"❓ DEBUG: Potential Chase transaction not parsed on line {i+1}: '{line[:80]}...'")
                
                except Exception as e:
                    print(f"🚨 DEBUG: Error on Chase line {i+1}: {e}")
                    continue
            
            # IMPORTANT: Final assignment for any remaining Unknown transactions
            unknown_remaining = sum(1 for t in temp_transactions if t.get('Name') == 'Unknown')
            if unknown_remaining > 0:
                print(f"📊 DEBUG: {unknown_remaining} transactions still Unknown at end of page {page_num}")
                print(f"📊 DEBUG: Current global cardholder: '{self.global_current_cardholder}'")
                print(f"📊 DEBUG: Cardholders found on this page: {page_cardholders_found}")
                
                # Use the most recent cardholder (either from this page or global)
                final_cardholder = self.global_current_cardholder
                if page_cardholders_found:
                    final_cardholder = page_cardholders_found[-1]  # Use the last one found on this page
                
                if final_cardholder != "Unknown":
                    assigned_final = 0
                    for temp_trans in temp_transactions:
                        if temp_trans.get('Name') == 'Unknown':
                            temp_trans['Name'] = final_cardholder
                            assigned_final += 1
                            if assigned_final <= 3:
                                print(f"   🔄 FINAL ASSIGNMENT: '{final_cardholder}' to {temp_trans['Date']} {temp_trans['Merchant'][:20]}...")
                            elif assigned_final == 4:
                                print(f"   🔄 ... and {unknown_remaining - 3} more final assignments")
                    
                    print(f"✅ DEBUG: Assigned {assigned_final} remaining Unknown transactions to '{final_cardholder}'")
                else:
                    print(f"⚠️  DEBUG: No cardholder available for final assignment - {unknown_remaining} transactions will remain Unknown")
            
            transactions = temp_transactions
        
        except Exception as e:
            print(f"🚨 DEBUG: Error parsing Chase page {page_num}: {e}")
        
        print(f"📄 DEBUG: Chase page {page_num} completed - {len(transactions)} transactions")
        print(f"📄 DEBUG: Global cardholder after Chase page {page_num}: '{self.global_current_cardholder}'")
        
        # Show summary of names assigned
        name_counts = {}
        for trans in transactions:
            name = trans.get('Name', 'Unknown')
            name_counts[name] = name_counts.get(name, 0) + 1
        print(f"📊 DEBUG: Name distribution on page {page_num}: {name_counts}")
        
        return transactions
    

    # def is_valid_chase_cardholder_name(self, name):
    #     """Validate if a string is likely a Chase cardholder name"""
    #     try:
    #         if not name or len(name.strip()) < 3:
    #             print(f"      🔍 CHASE VALIDATION: '{name}' - TOO SHORT")
    #             return False
                
    #         name = name.strip()
    #         words = name.split()
            
    #         # Must have at least 2 words (first and last name)
    #         if len(words) < 2 or len(words) > 5:  # Chase allows slightly longer names
    #             print(f"      🔍 CHASE VALIDATION: '{name}' - WRONG WORD COUNT ({len(words)})")
    #             return False
            
    #         # Must be all uppercase (Chase format)
    #         if not name.isupper():
    #             print(f"      🔍 CHASE VALIDATION: '{name}' - NOT UPPERCASE")
    #             return False
            
    #         # Each word should be alphabetic (with exceptions)
    #         valid_parts = ['JR', 'SR', 'III', 'IV', 'II', 'DE', 'LA', 'DEL', 'VON', 'VAN', 'MC', 'MAC']
    #         for word in words:
    #             if not (word.isalpha() or word in valid_parts):
    #                 print(f"      🔍 CHASE VALIDATION: '{name}' - NON-ALPHA: {word}")
    #                 return False
            
    #         # Check word lengths
    #         for word in words:
    #             if len(word) < 2 or len(word) > 15:
    #                 print(f"      🔍 CHASE VALIDATION: '{name}' - BAD LENGTH: {word}")
    #                 return False
            
    #         # Check for vowels in short words
    #         for word in words:
    #             if len(word) <= 3 and not any(vowel in word for vowel in 'AEIOU'):
    #                 print(f"      🔍 CHASE VALIDATION: '{name}' - NO VOWELS: {word}")
    #                 return False
            
    #         # Chase-specific false positives
    #         chase_false_positives = [
    #             'ACCOUNT SUMMARY', 'ACCOUNT ACTIVITY', 'ACCOUNT MESSAGES', 'ACCOUNT NUMBER',
    #             'CHASE ULTIMATE', 'ULTIMATE REWARDS', 'CUSTOMER SERVICE', 'PAYMENT DUE',
    #             'NEW BALANCE', 'MINIMUM PAYMENT', 'TRANSACTIONS THIS', 'INCLUDING PAYMENTS',
    #             'PREVIOUS BALANCE', 'CASH ADVANCES', 'BALANCE TRANSFERS', 'INTEREST CHARGED',
    #             'LATE PAYMENT', 'OVERLIMIT FEE', 'ANNUAL FEE', 'FINANCE CHARGE',
    #             'SERVICE STATION', 'GAS STATION', 'GROCERY STORE', 'DEPARTMENT STORE',
    #             'FAST FOOD', 'RESTAURANT', 'COFFEE SHOP', 'AUTO PARTS', 'HOME DEPOT'
    #         ]
            
    #         for fp in chase_false_positives:
    #             if fp in name.upper():
    #                 print(f"      🔍 CHASE VALIDATION: '{name}' - FALSE POSITIVE: {fp}")
    #                 return False
            
    #         # Business terms specific to Chase statements
    #         chase_business_terms = ['LLC', 'INC', 'CORP', 'LTD', 'CO', 'STORE', 'SHOP', 'MARKET', 'CENTER']
    #         for word in words:
    #             if word in chase_business_terms:
    #                 print(f"      🔍 CHASE VALIDATION: '{name}' - BUSINESS TERM: {word}")
    #                 return False
            
    #         print(f"      ✅ CHASE VALIDATION: '{name}' - PASSED")
    #         return True
            
    #     except Exception as e:
    #         print(f"      🚨 CHASE VALIDATION ERROR: {e}")
    #         return False
    
    # def extract_chase_cardholder_name(self, current_line, all_lines, current_index):
    #     """Enhanced Chase cardholder name extraction with better debugging"""
    #     try:
    #         print(f"🔍 DEBUG: Checking Chase name pattern on line {current_index + 1}: '{current_line}'")
            
    #         # Pattern 1: Look for "TRANSACTIONS THIS CYCLE (CARD XXXX)" pattern
    #         if 'TRANSACTIONS THIS CYCLE' in current_line.upper() and 'CARD' in current_line.upper():
    #             print(f"   📋 Found TRANSACTIONS THIS CYCLE pattern")
                
    #             # Extract card number for validation
    #             card_match = re.search(r'CARD\s+(\d+)', current_line.upper())
    #             if card_match:
    #                 card_number = card_match.group(1)
    #                 print(f"   💳 Card number found: {card_number}")
                
    #             # The name should be on the previous line(s)
    #             potential_name = None
                
    #             # Check previous line for name
    #             if current_index > 0:
    #                 prev_line = all_lines[current_index - 1].strip()
    #                 print(f"   🔎 Checking previous line for name: '{prev_line}'")
                    
    #                 if self.is_valid_chase_cardholder_name(prev_line):
    #                     potential_name = prev_line.strip()
    #                     print(f"   ✅ VALID CHASE NAME: '{potential_name}' (from previous line)")
    #                     return potential_name
    #                 else:
    #                     print(f"   ❌ Previous line failed validation: '{prev_line}'")
                
    #             # Check 2 lines back in case there's a blank line
    #             if current_index > 1:
    #                 prev_prev_line = all_lines[current_index - 2].strip()
    #                 print(f"   🔎 Checking 2 lines back for name: '{prev_prev_line}'")
                    
    #                 if self.is_valid_chase_cardholder_name(prev_prev_line):
    #                     potential_name = prev_prev_line.strip()
    #                     print(f"   ✅ VALID CHASE NAME: '{potential_name}' (from 2 lines back)")
    #                     return potential_name
    #                 else:
    #                     print(f"   ❌ 2 lines back failed validation: '{prev_prev_line}'")
                
    #             # Check 3 lines back
    #             if current_index > 2:
    #                 prev_prev_prev_line = all_lines[current_index - 3].strip()
    #                 print(f"   🔎 Checking 3 lines back for name: '{prev_prev_prev_line}'")
                    
    #                 if self.is_valid_chase_cardholder_name(prev_prev_prev_line):
    #                     potential_name = prev_prev_prev_line.strip()
    #                     print(f"   ✅ VALID CHASE NAME: '{potential_name}' (from 3 lines back)")
    #                     return potential_name
            
    #         # Pattern 2: Look for name followed by "TRANSACTIONS THIS CYCLE" on the SAME line
    #         if 'TRANSACTIONS THIS CYCLE' in current_line.upper():
    #             # Split by "TRANSACTIONS" to get the name part
    #             parts = current_line.split('TRANSACTIONS THIS CYCLE')
    #             if len(parts) > 0:
    #                 potential_name = parts[0].strip()
    #                 print(f"   🔎 Extracted name from same line: '{potential_name}'")
                    
    #                 if self.is_valid_chase_cardholder_name(potential_name):
    #                     print(f"   ✅ VALID CHASE NAME: '{potential_name}' (same line)")
    #                     return potential_name
    #                 else:
    #                     print(f"   ❌ Same line name failed validation: '{potential_name}'")
            
    #         # Pattern 3: Look for isolated name lines
    #         if (len(current_line.split()) >= 2 and 
    #             len(current_line.split()) <= 4 and
    #             current_line.isupper() and
    #             not any(char.isdigit() for char in current_line) and
    #             len(current_line) <= 40):
                
    #             print(f"   📋 Checking isolated name candidate: '{current_line}'")
                
    #             # Check if the next few lines contain "TRANSACTIONS THIS CYCLE" or transaction patterns
    #             found_supporting_evidence = False
    #             for check_ahead in range(1, 8):  # Check next 7 lines
    #                 if current_index + check_ahead < len(all_lines):
    #                     future_line = all_lines[current_index + check_ahead]
    #                     if ('TRANSACTIONS THIS CYCLE' in future_line.upper() or
    #                         # Look for transaction patterns (date + amount)
    #                         (re.search(r'^\d{1,2}/\d{1,2}', future_line) and re.search(r'\d+\.\d{2}$', future_line))):
    #                         found_supporting_evidence = True
    #                         print(f"   📊 Found supporting evidence {check_ahead} lines ahead: '{future_line[:50]}...'")
    #                         break
                
    #             if found_supporting_evidence and self.is_valid_chase_cardholder_name(current_line):
    #                 print(f"   ✅ VALID CHASE NAME: '{current_line}' (isolated, with supporting evidence)")
    #                 return current_line.strip()
    #             elif found_supporting_evidence:
    #                 print(f"   ❌ Isolated name failed validation: '{current_line}'")
            
    #         print(f"   ❌ NO CHASE NAME FOUND")
    #         return None
            
    #     except Exception as e:
    #         print(f"   🚨 ERROR in extract_chase_cardholder_name: {e}")
    #         return None

    # def parse_chase_transaction_line(self, line):
    #     """Parse individual Chase transaction line with enhanced debugging"""
    #     try:
    #         # Chase format: MM/DD [&] MERCHANT_NAME LOCATION AMOUNT
    #         date_pattern = r'^(\d{1,2}/\d{1,2})\s*(&?)\s*(.+?)\s+([-]?\d{1,}(?:,\d{3})*\.\d{2})$'
            
    #         match = re.match(date_pattern, line)
            
    #         if match:
    #             date = match.group(1)
    #             merchant_and_location = match.group(3).strip()
    #             amount = match.group(4)
                
    #             # Clean up merchant name
    #             merchant_desc = re.sub(r'\s+', ' ', merchant_and_location)
    #             merchant_desc = re.sub(r'\s+[A-Z]{2}$', '', merchant_desc)  # Remove state codes
    #             merchant_desc = re.sub(r'\s+\d{3}-\d{3}-\d{4}$', '', merchant_desc)  # Remove phone numbers
    #             merchant_desc = re.sub(r'\s+\d{10,}$', '', merchant_desc)  # Remove long numbers
                
    #             # Skip negative amounts (payments/credits)
    #             try:
    #                 amount_value = float(amount.replace(',', ''))  # Remove commas before parsing!
    #                 if amount_value <= 0:
    #                     return None  # Skip payments and credits
    #             except ValueError:
    #                 return None  # Skip if amount can't be parsed
                
    #             # Get the correct year based on the date range
    #             transaction_month = int(date.split('/')[0])
    #             correct_year = self.get_chase_transaction_year(transaction_month)
    #             full_date = f"{date}/{correct_year}"
                
    #             return {
    #                 'Date': full_date,
    #                 'Merchant': merchant_desc,
    #                 'Amount': amount
    #             }
        
    #     except Exception:
    #         pass
        
    #     return None
    
    def process_all_pdfs(self):
        """Process all PDFs and create combined Excel files with validation"""
        self.update_progress("🚀 Starting PDF processing...", "Initializing conversion process")
        start_time = time.time()
        
        try:
            self.setup_folders()
            
            # Get all PDF files
            pdf_files = []
            try:
                pdf_files = [f for f in os.listdir(self.convert_folder) if f.lower().endswith('.pdf')]
            except Exception:
                self.update_progress("❌ Could not access Convert folder", "")
                return 0, 0
            
            if not pdf_files:
                self.update_progress("❌ No PDF files found", "Add PDFs to Convert folder and try again")
                return 0, 0
            
            self.update_progress(f"📁 Found {len(pdf_files)} PDF file(s)", f"Files: {', '.join(pdf_files)}", force_update=True)
            
            # Separate data by statement type
            amex_data = []
            chase_data = []
            
            for i, pdf_file in enumerate(pdf_files, 1):
                try:
                    pdf_path = os.path.join(self.convert_folder, pdf_file)
                    self.update_progress(f"📄 Processing PDF {i}/{len(pdf_files)}", f"{pdf_file}", force_update=True)
                    
                    data, statement_type = self.extract_pdf_content(pdf_path)
                    
                    if data:
                        if statement_type == 'amex':
                            amex_data.extend(data)
                        elif statement_type == 'chase':
                            chase_data.extend(data)
                        
                        # Only update totals, not every transaction
                        self.update_progress(f"✅ Extracted {len(data)} transactions", "", force_update=True)
                    else:
                        self.update_progress(f"❌ Failed to extract data from {pdf_file}", "", force_update=True)
                
                except Exception as e:
                    self.update_progress(f"❌ Error processing {pdf_file}", f"Error: {str(e)}", force_update=True)
                    continue
            
            self.update_progress("📈 Creating Excel files...", 
                               f"AmEx: {len(amex_data)}, Chase: {len(chase_data)} transactions", force_update=True)
            
            # Create Excel files
            files_created = 0
            
            if amex_data:
                self.update_progress("📝 Creating AmEx Excel file...", "", force_update=True)
                success = self.create_excel_file(amex_data, 'AmEx_Combined')
                if success:
                    files_created += 1
            
            if chase_data:
                self.update_progress("📝 Creating Chase Excel file...", "", force_update=True)
                success = self.create_excel_file(chase_data, 'Chase_Combined')
                if success:
                    files_created += 1
            
            # Generate validation report BEFORE returning
            try:
                if hasattr(self, 'validator') and self.validator.validation_results:
                    self.update_progress("📋 Creating validation report...", "", force_update=True)
                    self.create_validation_report()
            except Exception as e:
                print(f"❌ Error creating validation report: {e}")
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            total_transactions = len(amex_data) + len(chase_data)
            self.update_progress("🎉 Processing Complete!", 
                               f"Files: {files_created}, Transactions: {total_transactions}", force_update=True)
            
            return files_created, total_transactions
        
        except Exception as e:
            self.update_progress("❌ Unexpected error occurred", f"Error: {str(e)}")
            return 0, 0
    
    # def create_excel_file(self, data, filename_base):
    #     """Create Excel file with extracted data"""
    #     try:
    #         df = pd.DataFrame(data)
            
    #         if df.empty:
    #             self.update_progress(f"❌ No data for {filename_base}", "")
    #             return False
            
    #         # Generate filename
    #         timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    #         excel_filename = f"{filename_base}_{timestamp}.xlsx"
    #         excel_path = os.path.join(self.excel_folder, excel_filename)
            
    #         try:
    #             with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
    #                 # Write data to Excel
    #                 df.to_excel(writer, sheet_name='Transactions', index=False)
                    
    #                 # Get worksheet for formatting
    #                 worksheet = writer.sheets['Transactions']
                    
    #                 # Auto-adjust column widths
    #                 for column in worksheet.columns:
    #                     max_length = 0
    #                     column_letter = column[0].column_letter
    #                     for cell in column:
    #                         try:
    #                             if len(str(cell.value)) > max_length:
    #                                 max_length = len(str(cell.value))
    #                         except Exception:
    #                             pass
    #                     adjusted_width = min(max_length + 2, 50)
    #                     worksheet.column_dimensions[column_letter].width = adjusted_width
                
    #             self.update_progress(f"✅ Created {excel_filename}", "", force_update=True)
    #             return True
                
    #         except Exception as e:
    #             self.update_progress(f"❌ Error creating {filename_base}", f"Error: {str(e)}")
    #             return False
        
    #     except Exception as e:
    #         self.update_progress(f"❌ Error in create_excel_file", f"Error: {str(e)}")
    #         return False


    def extract_pdf_content(self, pdf_path):
        """Extract transaction data with global cardholder tracking"""
        extracted_data = []
        statement_type = 'unknown'
        
        # GLOBAL: Track cardholder across the ENTIRE document
        self.global_current_cardholder = "Unknown"
        
        self.update_progress("📄 Reading PDF content...", f"Processing: {os.path.basename(pdf_path)}", force_update=True)
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Get full text for detection and date extraction
                full_text = ""
                for page in pdf.pages:
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            full_text += page_text + "\n"
                    except Exception:
                        continue
                
                filename = os.path.basename(pdf_path)
                statement_type = self.detect_statement_type(full_text, filename)
                self.update_progress(f"🔍 Detected: {statement_type}", "", force_update=True)
                
                # Extract date range for Chase statements
                if statement_type == 'chase':
                    self.chase_date_range = self.extract_chase_date_range(full_text)
                
                # Extract transactions from all pages
                self.update_progress(f"📖 Processing {len(pdf.pages)} pages...", "", force_update=True)
                
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            if page_num % 5 == 1 or page_num == len(pdf.pages):
                                self.update_progress(f"📄 Processing page {page_num}...", "", force_update=True)
                            
                            if statement_type == 'amex':
                                page_transactions = self.parse_amex_page_global(page_text, page_num)
                            elif statement_type == 'chase':
                                page_transactions = self.parse_chase_page(page_text, page_num)
                            else:
                                continue
                            
                            extracted_data.extend(page_transactions)
                    except Exception as e:
                        continue
                
                # VALIDATION STEP
                if extracted_data and statement_type != 'unknown':
                    self.update_progress("🔍 Validating extraction...", "Checking for missed transactions", force_update=True)
                    validation_result = self.validator.validate_extraction(pdf_path, extracted_data, statement_type)
                    self.validator.validation_results[pdf_path] = validation_result
        
        except Exception as e:
            self.update_progress("❌ PDF processing error", f"Error: {str(e)}")
            return None, statement_type
            
        return extracted_data, statement_type

    # def parse_amex_page_global(self, page_text, page_num):
    #     """Parse AmEx page using global cardholder tracking"""
    #     transactions = []
        
    #     print(f"\n📄 DEBUG: Starting page {page_num} with global cardholder: '{self.global_current_cardholder}'")
        
    #     try:
    #         lines = page_text.split('\n')
    #         print(f"📄 DEBUG: Page {page_num} has {len(lines)} lines")
            
    #         for i, line in enumerate(lines):
    #             try:
    #                 line = line.strip()
                    
    #                 # Skip empty lines
    #                 if len(line) < 5:
    #                     continue
                    
    #                 # Skip obvious headers
    #                 if (('Merchant Name' in line and '$ Amount' in line) or
    #                     'Date of Transaction' in line or
    #                     line.startswith('Amazon Business Prime Card') or
    #                     line.startswith('AMERICAN EXPRESS') or
    #                     line.startswith('Page ') or
    #                     line.startswith('Customer Care')):
    #                     continue
                    
    #                 # Check for continuation headers - preserve current name
    #                 if self.is_continuation_header(line):
    #                     print(f"📋 DEBUG: Continuation header on line {i+1}: '{line}'")
    #                     print(f"   🔄 PRESERVING global cardholder: '{self.global_current_cardholder}'")
    #                     continue
                    
    #                 # Check for new cardholder name
    #                 cardholder_name = self.extract_cardholder_name(line)
    #                 if cardholder_name:
    #                     old_cardholder = self.global_current_cardholder
    #                     self.global_current_cardholder = cardholder_name
    #                     print(f"🏷️  DEBUG: GLOBAL CARDHOLDER CHANGED on line {i+1}")
    #                     print(f"   FROM: '{old_cardholder}' TO: '{self.global_current_cardholder}'")
    #                     continue
                    
    #                 # Parse transaction
    #                 transaction = self.parse_amex_transaction_line(line)
    #                 if transaction:
    #                     # Use GLOBAL cardholder
    #                     transaction['Name'] = self.global_current_cardholder
    #                     transactions.append(transaction)
    #                     print(f"💳 DEBUG: Transaction on line {i+1}")
    #                     print(f"   ASSIGNED TO: '{self.global_current_cardholder}'")
    #                     print(f"   TRANSACTION: {transaction['Date']} | {transaction['Merchant'][:30]}... | ${transaction['Amount']}")
    #                 else:
    #                     # Show potential missed transactions
    #                     if (len(line) > 15 and 
    #                         any(char.isdigit() for char in line) and 
    #                         ('$' in line or re.search(r'\d+\.\d{2}', line)) and
    #                         not any(skip in line.upper() for skip in ['TOTAL', 'BALANCE', 'PAYMENT', 'CREDIT'])):
    #                         print(f"❓ DEBUG: Potential transaction not parsed on line {i+1}: '{line[:80]}...'")
                
    #             except Exception as e:
    #                 print(f"🚨 DEBUG: Error on line {i+1}: {e}")
    #                 continue
        
    #     except Exception as e:
    #         print(f"🚨 DEBUG: Error parsing page {page_num}: {e}")
        
    #     print(f"📄 DEBUG: Page {page_num} completed - {len(transactions)} transactions")
    #     print(f"📄 DEBUG: Global cardholder after page {page_num}: '{self.global_current_cardholder}'")
    #     return transactions

    # def is_continuation_header(self, line):
    #     """Check if line is a continuation header"""
    #     try:
    #         line_upper = line.strip().upper()
            
    #         continuation_patterns = [
    #             'DETAIL CONTINUED',
    #             'CONTINUED ON NEXT PAGE',
    #             'CONTINUED ON REVERSE',
    #             'ACCOUNT ACTIVITY (CONTINUED)',
    #             'ACCOUNT ACTIVITY CONTINUED',
    #             'TRANSACTIONS THIS CYCLE',
    #             'INCLUDING PAYMENTS RECEIVED',
    #             'CONTINUED FROM PREVIOUS PAGE',
    #             'AMOUNT'
    #         ]
            
    #         for pattern in continuation_patterns:
    #             if pattern in line_upper:
    #                 return True
            
    #         # Check for account ending lines in continuation sections
    #         if ('ACCOUNT ENDING' in line_upper and 
    #             len(line.split()) >= 3 and 
    #             any(char.isdigit() for char in line)):
    #             return True
            
    #         return False
            
    #     except Exception:
    #         return False

    # def extract_cardholder_name(self, line):
    #     """Extract cardholder name with enhanced debugging"""
    #     try:
    #         line = line.strip()
            
    #         print(f"🔍 DEBUG: Analyzing line: '{line}'")
            
    #         # Skip continuation headers first
    #         if self.is_continuation_header(line):
    #             print(f"   🔄 SKIPPED: Continuation header")
    #             return None
            
    #         # Skip lines with obvious non-name content
    #         skip_patterns = [
    #             'Amount', '$', 'Date', 'Merchant', 'Transaction', 'Account', 'Page',
    #             'Statement', 'Balance', 'Payment', 'Interest', 'Fee', 'Charge',
    #             'Credit', 'Debit', 'Purchase', 'Cash', 'Advance', 'Transfer',
    #             'www.', 'http', '.com', '@', '#', '*', '&', '%', 
    #             'Detail', 'Continued', 'Including', 'Payments', 'Received',
    #             '/', '-', '(', ')', '[', ']', '{', '}', '|', '\\'
    #         ]
            
    #         skip_found = [pattern for pattern in skip_patterns if pattern in line]
    #         if skip_found:
    #             print(f"   ⏭️  SKIPPED: Contains: {skip_found}")
    #             return None
            
    #         # Pattern 1: "NAME Card Ending X-XXXXX"
    #         if 'Card Ending' in line:
    #             print(f"   📋 Pattern 1: Card Ending found")
                
    #             if any(word in line.upper() for word in ['CONTINUED', 'DETAIL', 'INCLUDING']):
    #                 print(f"   ⏭️  SKIPPED: In continuation context")
    #                 return None
                
    #             parts = line.split('Card Ending')
    #             if parts:
    #                 potential_name = parts[0].strip()
    #                 print(f"   🔎 Extracted: '{potential_name}'")
    #                 if self.is_valid_cardholder_name(potential_name):
    #                     print(f"   ✅ VALID: '{potential_name}' (Pattern 1)")
    #                     return potential_name
    #                 else:
    #                     print(f"   ❌ INVALID: '{potential_name}'")
            
    #         # Pattern 2: Standalone name lines
    #         words = line.split()
    #         if (2 <= len(words) <= 3 and 
    #             line.isupper() and 
    #             len(line) <= 30 and
    #             not any(char.isdigit() for char in line)):
                
    #             print(f"   📋 Pattern 2: Standalone name candidate")
                
    #             if any(word in line.upper() for word in ['CONTINUED', 'DETAIL', 'INCLUDING', 'AMOUNT']):
    #                 print(f"   ⏭️  SKIPPED: Near continuation keywords")
    #                 return None
                
    #             if self.is_valid_cardholder_name(line):
    #                 print(f"   ✅ VALID: '{line}' (Pattern 2)")
    #                 return line.strip()
    #             else:
    #                 print(f"   ❌ INVALID: '{line}'")
            
    #         # Pattern 3: Name + account info
    #         if len(words) >= 3:
    #             print(f"   📋 Pattern 3: Name + account info")
                
    #             if any(word in line.upper() for word in ['CONTINUED', 'DETAIL', 'INCLUDING']):
    #                 print(f"   ⏭️  SKIPPED: In continuation context")
    #                 return None
                
    #             # Try 2-word names
    #             potential_name = ' '.join(words[:2])
    #             remaining = ' '.join(words[2:]).upper()
    #             account_keywords = ['CARD', 'ACCOUNT', 'ENDING', 'AMOUNT']
    #             found_keywords = [kw for kw in account_keywords if kw in remaining]
                
    #             if self.is_valid_cardholder_name(potential_name) and found_keywords:
    #                 print(f"   ✅ VALID: '{potential_name}' (Pattern 3)")
    #                 return potential_name
                
    #             # Try 3-word names
    #             if len(words) >= 4:
    #                 potential_name = ' '.join(words[:3])
    #                 remaining = ' '.join(words[3:]).upper()
    #                 found_keywords = [kw for kw in account_keywords if kw in remaining]
                    
    #                 if self.is_valid_cardholder_name(potential_name) and found_keywords:
    #                     print(f"   ✅ VALID: '{potential_name}' (Pattern 3)")
    #                     return potential_name
            
    #         print(f"   ❌ NO NAME FOUND")
    #         return None
                                
    #     except Exception as e:
    #         print(f"   🚨 ERROR: {e}")
    #         return None

    # def is_valid_cardholder_name(self, name):
    #     """Enhanced name validation with detailed logging"""
    #     try:
    #         if not name or len(name.strip()) < 3:
    #             print(f"      🔍 VALIDATION: '{name}' - TOO SHORT")
    #             return False
                
    #         name = name.strip()
    #         words = name.split()
            
    #         if len(words) < 2 or len(words) > 4:
    #             print(f"      🔍 VALIDATION: '{name}' - WRONG WORD COUNT ({len(words)})")
    #             return False
            
    #         if not name.isupper():
    #             print(f"      🔍 VALIDATION: '{name}' - NOT UPPERCASE")
    #             return False
            
    #         # Check alphabetic characters
    #         valid_parts = ['JR', 'SR', 'III', 'IV', 'II', 'DE', 'LA', 'DEL', 'VON', 'VAN', 'MC', 'MAC']
    #         for word in words:
    #             if not (word.isalpha() or word in valid_parts):
    #                 print(f"      🔍 VALIDATION: '{name}' - NON-ALPHA: {word}")
    #                 return False
            
    #         # Check word lengths
    #         for word in words:
    #             if len(word) < 2 or len(word) > 15:
    #                 print(f"      🔍 VALIDATION: '{name}' - BAD LENGTH: {word}")
    #                 return False
            
    #         # Check for vowels in short words (avoid acronyms)
    #         for word in words:
    #             if len(word) <= 3 and not any(vowel in word for vowel in 'AEIOU'):
    #                 print(f"      🔍 VALIDATION: '{name}' - NO VOWELS: {word}")
    #                 return False
            
    #         # Comprehensive false positive list
    #         false_positives = [
    #             'ACCOUNT ENDING', 'CARD ENDING', 'CUSTOMER CARE', 'AMAZON BUSINESS',
    #             'AMERICAN EXPRESS', 'PAYMENT TERMS', 'NEW CHARGES', 'TOTAL BALANCE',
    #             'MINIMUM PAYMENT', 'INTEREST CHARGED', 'DETAIL CONTINUED', 'AMOUNT ENCLOSED',
    #             'SERVICE STN', 'FAST FOOD', 'RESTAURANT', 'GAS STATION', 'AUTO PAY',
    #             'GROCERY OUTLET', 'UNION', 'CHEVRON', 'SHELL OIL', 'MOBILE', 'ARCO',
    #             'SAFEWAY', 'COSTCO', 'TARGET', 'WALMART', 'HOME DEPOT'
    #         ]
            
    #         for fp in false_positives:
    #             if fp in name.upper():
    #                 print(f"      🔍 VALIDATION: '{name}' - FALSE POSITIVE: {fp}")
    #                 return False
            
    #         # Business terms
    #         business_terms = [
    #             'STN', 'LLC', 'INC', 'CORP', 'LTD', 'CO', 'STORE', 'SHOP',
    #             'MARKET', 'CENTER', 'DEPOT', 'STATION', 'FUEL', 'GAS', 'OIL'
    #         ]
            
    #         for word in words:
    #             if word in business_terms:
    #                 print(f"      🔍 VALIDATION: '{name}' - BUSINESS TERM: {word}")
    #                 return False
            
    #         print(f"      ✅ VALIDATION: '{name}' - PASSED")
    #         return True
            
    #     except Exception as e:
    #         print(f"      🚨 VALIDATION ERROR: {e}")
    #         return False

    def create_excel_file(self, data, filename_base):
        """Create Excel file with names column"""
        try:
            df = pd.DataFrame(data)
            
            if df.empty:
                self.update_progress(f"❌ No data for {filename_base}", "")
                return False
            
            # Reorder columns: Name, Date, Merchant, Amount
            if 'Name' in df.columns:
                column_order = ['Name', 'Date', 'Merchant', 'Amount']
                existing_columns = [col for col in column_order if col in df.columns]
                df = df[existing_columns]
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            excel_filename = f"{filename_base}_{timestamp}.xlsx"
            excel_path = os.path.join(self.excel_folder, excel_filename)
            
            try:
                with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Transactions', index=False)
                    
                    # Auto-adjust column widths
                    worksheet = writer.sheets['Transactions']
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except Exception:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
                
                self.update_progress(f"✅ Created {excel_filename}", "", force_update=True)
                return True
                
            except Exception as e:
                self.update_progress(f"❌ Error creating {filename_base}", f"Error: {str(e)}")
                return False
        
        except Exception as e:
            self.update_progress(f"❌ Error in create_excel_file", f"Error: {str(e)}")
            return False

# def show_completion_message(files_created, total_transactions):
#     """Show completion message using GUI"""
#     try:
#         import tkinter as tk
#         from tkinter import messagebox
        
#         # Create a hidden root window
#         root = tk.Tk()
#         root.withdraw()
        
#         # Show completion message
#         if files_created > 0:
#             message = f"✅ SUCCESS!\n\n" \
#                      f"Created {files_created} Excel file(s)\n" \
#                      f"Processed {total_transactions} transactions\n\n" \
#                      f"Check the 'Excel' folder for your results!"
#             title = "PDF to Excel Conversion - Complete"
#         else:
#             message = "⚠️ No Excel files were created.\n\n" \
#                      "Please check that your PDFs contain transaction data\n" \
#                      "and try again."
#             title = "PDF to Excel Conversion - No Data Found"
        
#         messagebox.showinfo(title, message)
#         root.destroy()
        
#     except Exception:
#         # Fallback: console message
#         try:
#             if files_created > 0:
#                 print(f"✅ SUCCESS! Created {files_created} Excel file(s), Processed {total_transactions} transactions")
#             else:
#                 print("⚠️ No Excel files were created.")
#         except Exception:
#             pass

def main():
    try:
        converter = UniversalPDFToExcelConverter()
        
        # Show progress window
        progress_window = converter.show_progress_window()
        
        files_created = 0
        total_transactions = 0
        
        try:
            if progress_window:
                # Run conversion directly in main thread to avoid variable scope issues
                files_created, total_transactions = converter.process_all_pdfs()
            else:
                # Fallback: run without GUI
                files_created, total_transactions = converter.process_all_pdfs()
                
        except Exception as e:
            converter.update_progress("❌ Critical error", f"Error: {str(e)}")
        
        # Close progress window
        converter.close_progress_window()
        
        # Show completion message with validation info
        show_completion_message_with_validation(converter, files_created, total_transactions)
        
    except Exception as e:
        try:
            print(f"Critical error: {str(e)}")
            time.sleep(3)
        except Exception:
            pass

def show_completion_message_with_validation(converter, files_created, total_transactions):
    """Enhanced completion message that includes validation summary"""
    try:
        import tkinter as tk
        from tkinter import messagebox
        
        # Create a hidden root window
        root = tk.Tk()
        root.withdraw()
        
        # Build validation summary
        validation_summary = ""
        if hasattr(converter, 'validator') and converter.validator.validation_results:
            validation_summary = "\n\n📊 VALIDATION SUMMARY:\n"
            
            total_files = len(converter.validator.validation_results)
            high_confidence = sum(1 for r in converter.validator.validation_results.values() if r['confidence_score'] >= 95)
            medium_confidence = sum(1 for r in converter.validator.validation_results.values() if 85 <= r['confidence_score'] < 95)
            low_confidence = sum(1 for r in converter.validator.validation_results.values() if r['confidence_score'] < 85)
            
            validation_summary += f"🟢 Excellent (95%+): {high_confidence} files\n"
            validation_summary += f"🟡 Good (85-94%): {medium_confidence} files\n"
            validation_summary += f"🔴 Needs Review (<85%): {low_confidence} files\n"
            
            # Count total potential issues
            total_missed = sum(len(r['potential_missed']) for r in converter.validator.validation_results.values())
            amount_issues = sum(1 for r in converter.validator.validation_results.values() if r['amount_discrepancy'])
            
            if total_missed > 0 or amount_issues > 0:
                validation_summary += f"\n⚠️  Issues Found:\n"
                if total_missed > 0:
                    validation_summary += f"   • {total_missed} potentially missed transactions\n"
                if amount_issues > 0:
                    validation_summary += f"   • {amount_issues} files with amount discrepancies\n"
                validation_summary += "\nCheck validation report for details!"
            else:
                validation_summary += "\n✅ No issues detected!"
        
        # Show completion message
        if files_created > 0:
            message = f"✅ SUCCESS!\n\n" \
                     f"Created {files_created} Excel file(s)\n" \
                     f"Processed {total_transactions} transactions\n\n" \
                     f"Check the 'Excel' folder for your results!" + validation_summary
            title = "PDF to Excel Conversion - Complete"
        else:
            message = "⚠️ No Excel files were created.\n\n" \
                     "Please check that your PDFs contain transaction data\n" \
                     "and try again." + validation_summary
            title = "PDF to Excel Conversion - No Data Found"
        
        messagebox.showinfo(title, message)
        root.destroy()
        
    except Exception:
        # Fallback: console message
        try:
            if files_created > 0:
                print(f"✅ SUCCESS! Created {files_created} Excel file(s), Processed {total_transactions} transactions")
                if hasattr(converter, 'validator') and converter.validator.validation_results:
                    print("📋 Validation report created - check Excel folder for details!")
            else:
                print("⚠️ No Excel files were created.")
        except Exception:
            pass

if __name__ == "__main__":
    main()