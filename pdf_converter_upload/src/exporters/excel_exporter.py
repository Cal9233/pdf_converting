"""
Excel export utilities for PDF to Excel Converter

This module handles Excel file creation and validation report generation.
"""

import os
import pandas as pd
from datetime import datetime

from config import (
    EXCEL_COLUMN_ORDER,       # ['Name', 'Date', 'Merchant', 'Amount']
    TIMESTAMP_FORMAT,         # '%Y%m%d_%H%M%S'
    MAX_COLUMN_WIDTH,         # 50
    COLUMN_WIDTH_PADDING      # 2
)


class ExcelExporter:
    """Handles Excel file creation and validation reports"""
    
    def __init__(self, excel_folder="Excel"):
        """Initialize the Excel exporter with output folder"""
        self.excel_folder = excel_folder

    def create_excel_file(self, data, filename_base):
        """Create Excel file with extracted data"""
        try:
            df = pd.DataFrame(data)
            
            if df.empty:
                print(f"❌ No data for {filename_base}")
                return False
            
            # Reorder columns using config
            if 'Name' in df.columns:
                existing_columns = [col for col in EXCEL_COLUMN_ORDER if col in df.columns]
                df = df[existing_columns]
            
            # Generate filename using config timestamp format
            timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
            excel_filename = f"{filename_base}_{timestamp}.xlsx"
            excel_path = os.path.join(self.excel_folder, excel_filename)
            
            try:
                with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Transactions', index=False)
                    
                    # Auto-adjust column widths using config values
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
                        adjusted_width = min(max_length + COLUMN_WIDTH_PADDING, MAX_COLUMN_WIDTH)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
                
                print(f"✅ Created {excel_filename}")
                return True
                
            except Exception as e:
                print(f"❌ Error creating {filename_base}: {str(e)}")
                return False
        
        except Exception as e:
            print(f"❌ Error in create_excel_file: {str(e)}")
            return False

    def create_validation_report(self, validation_results):
        """Create a comprehensive validation report"""
        # Use config timestamp format for validation report filename
        report_path = os.path.join(self.excel_folder, f"Validation_Report_{datetime.now().strftime(TIMESTAMP_FORMAT)}.txt")
        
        try:
            with open(report_path, 'w') as f:
                f.write("PDF TO EXCEL CONVERSION - VALIDATION REPORT\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                for pdf_path, result in validation_results.items():
                    f.write(f"FILE: {result['pdf_file']}\n")
                    f.write("-" * 30 + "\n")
                    f.write(f"Statement Type: {result['statement_type'].upper()}\n")
                    f.write(f"Extracted: {result['extracted_count']} transactions\n")
                    f.write(f"Estimated Total: {result['estimated_total']} transactions\n")
                    f.write(f"Confidence Score: {result['confidence_score']}%\n")
                    
                    if result['amount_discrepancy']:
                        disc = result['amount_discrepancy']
                        f.write(f"Amount Discrepancy: ${disc['difference']:,.2f}\n")
                    
                    if result['potential_missed']:
                        f.write(f"Potential Missed: {len(result['potential_missed'])} transactions\n")
                        f.write("Details:\n")
                        for missed in result['potential_missed']:
                            f.write(f"  Page {missed['page']}: {missed['text']}\n")
                    
                    f.write("\n")
                
            print(f"\n📋 Validation report saved: {report_path}")
            
        except Exception as e:
            print(f"❌ Error creating validation report: {e}")