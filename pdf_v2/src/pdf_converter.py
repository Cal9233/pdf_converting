"""Main PDF to Excel converter."""

import os
from datetime import datetime
from typing import List, Dict
import pandas as pd

from src.amex_parser import AmexParser
from src.chase_parser import ChaseParser
from config.settings import EXCEL_COLUMN_WIDTHS


class PDFConverter:
    """Convert PDF bank statements to Excel."""
    
    def __init__(self, input_dir: str = 'data', output_dir: str = 'output'):
        self.input_dir = input_dir
        self.output_dir = output_dir
        
        # Create directories if they don't exist
        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
    def convert_all(self):
        """Convert all PDFs in the input directory, creating one Excel file per subdirectory."""
        # Get subdirectories in data folder
        subdirs = self._get_subdirectories()
        
        if not subdirs:
            print("No subdirectories found in the input directory.")
            return
            
        total_files_processed = 0
        
        for subdir in subdirs:
            print(f"\n{'='*60}")
            print(f"Processing {subdir.upper()} statements...")
            print(f"{'='*60}")
            
            # Find PDFs in this subdirectory
            pdf_files = self._find_pdf_files_in_subdir(subdir)
            
            if not pdf_files:
                print(f"No PDF files found in {subdir}/ directory.")
                continue
                
            subdir_transactions = []
            
            for pdf_file in pdf_files:
                print(f"\nProcessing: {pdf_file}")
                
                # Determine parser based on subdirectory name
                parser = self._get_parser_for_subdir(subdir, pdf_file)
                if not parser:
                    print(f"  ⚠️  Could not determine parser for: {pdf_file}")
                    continue
                    
                # Parse the PDF
                try:
                    transactions = parser.parse_pdf(pdf_file)
                    print(f"  ✓ Extracted {len(transactions)} transactions")
                    subdir_transactions.extend(transactions)
                    total_files_processed += 1
                except Exception as e:
                    print(f"  ✗ Error parsing {pdf_file}: {str(e)}")
                    
            # Save to Excel for this subdirectory
            if subdir_transactions:
                self._save_to_excel(subdir_transactions, subdir)
            else:
                print(f"\nNo transactions found in {subdir}/ to export.")
                
        if total_files_processed == 0:
            print("\nNo PDF files were successfully processed.")
        else:
            print(f"\n{'='*60}")
            print(f"Total files processed: {total_files_processed}")
    
    def _get_subdirectories(self) -> List[str]:
        """Get all subdirectories in the input directory."""
        subdirs = []
        
        if os.path.exists(self.input_dir):
            for item in os.listdir(self.input_dir):
                path = os.path.join(self.input_dir, item)
                if os.path.isdir(path):
                    subdirs.append(item)
                    
        return sorted(subdirs)
    
    def _find_pdf_files_in_subdir(self, subdir: str) -> List[str]:
        """Find all PDF files in a specific subdirectory."""
        pdf_files = []
        subdir_path = os.path.join(self.input_dir, subdir)
        
        if os.path.exists(subdir_path):
            for file in os.listdir(subdir_path):
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(subdir_path, file))
                    
        return sorted(pdf_files)
    
    def _get_parser_for_subdir(self, subdir: str, filename: str):
        """Get the appropriate parser based on subdirectory name."""
        subdir_lower = subdir.lower()
        
        if subdir_lower == 'amex':
            return AmexParser()
        elif subdir_lower == 'chase':
            return ChaseParser()
        elif subdir_lower == 'other':
            # For 'other' directory, try to determine from filename
            filename_lower = filename.lower()
            if 'amex' in filename_lower or 'american express' in filename_lower:
                return AmexParser()
            elif 'chase' in filename_lower:
                return ChaseParser()
            else:
                # Default to AmexParser for now (we'll create a generic parser later)
                print(f"  ℹ️  Using AmEx parser as default for: {filename}")
                return AmexParser()
        
        return None
    
    def _save_to_excel(self, transactions: List[Dict[str, str]], subdir: str):
        """Save transactions to Excel file with subdirectory name."""
        # Convert to DataFrame
        df = pd.DataFrame(transactions)
        
        # Ensure columns are in the right order
        df = df[['Name', 'Date', 'Merchant', 'Amount']]
        
        # Sort by Name and Date
        df = df.sort_values(['Name', 'Date'])
        
        # Generate filename with subdirectory name and timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(self.output_dir, f'{subdir}_transactions_{timestamp}.xlsx')
        
        # Create Excel writer
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Transactions', index=False)
            
            # Format the worksheet
            worksheet = writer.sheets['Transactions']
            
            # Set column widths
            for col, width in EXCEL_COLUMN_WIDTHS.items():
                col_letter = chr(65 + list(EXCEL_COLUMN_WIDTHS.keys()).index(col))
                worksheet.column_dimensions[col_letter].width = width
                
            # Format amount column as currency
            for row in range(2, len(df) + 2):
                worksheet[f'D{row}'].number_format = '$#,##0.00'
                
        print(f"\n✅ Exported {len(df)} transactions to: {output_file}")
        
        # Print summary
        print(f"\nSummary for {subdir.upper()}:")
        summary = df.groupby('Name').agg({
            'Amount': ['count', 'sum']
        }).round(2)
        summary.columns = ['Transaction Count', 'Total Amount']
        print(summary.to_string())