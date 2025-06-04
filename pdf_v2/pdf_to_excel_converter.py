#!/usr/bin/env python3
"""
Simple GUI version with just a progress window
"""

import os
import sys
import tkinter as tk
from tkinter import ttk
import threading
import time

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from src.amex_parser import AmexParser
from src.chase_parser import ChaseParser
from config.settings import EXCEL_COLUMN_WIDTHS
import pandas as pd
from datetime import datetime


class StandalonePDFConverter:
    """Base converter functionality"""
    
    def __init__(self):
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = current_dir
            
        self.input_dir = os.path.join(self.base_dir, 'Convert')
        self.output_dir = os.path.join(self.base_dir, 'Excel')
        
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        for subfolder in ['amex', 'chase', 'other']:
            os.makedirs(os.path.join(self.input_dir, subfolder), exist_ok=True)
    
    def _count_pdfs(self) -> int:
        """Count total PDF files in all subdirectories."""
        count = 0
        for subdir in ['amex', 'chase', 'other']:
            subdir_path = os.path.join(self.input_dir, subdir)
            if os.path.exists(subdir_path):
                count += len([f for f in os.listdir(subdir_path) if f.lower().endswith('.pdf')])
        return count
    
    def _get_subdirectories(self) -> list:
        """Get subdirectories."""
        return ['amex', 'chase', 'other']
    
    def _find_pdf_files_in_subdir(self, subdir: str) -> list:
        """Find PDF files in subdirectory."""
        pdf_files = []
        subdir_path = os.path.join(self.input_dir, subdir)
        if os.path.exists(subdir_path):
            for file in os.listdir(subdir_path):
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(subdir_path, file))
        return sorted(pdf_files)
    
    def _get_parser_for_subdir(self, subdir: str, filename: str):
        """Get appropriate parser."""
        subdir_lower = subdir.lower()
        
        if subdir_lower == 'amex':
            return AmexParser()
        elif subdir_lower == 'chase':
            return ChaseParser()
        elif subdir_lower == 'other':
            filename_lower = filename.lower()
            if 'amex' in filename_lower or 'american express' in filename_lower:
                return AmexParser()
            elif 'chase' in filename_lower:
                return ChaseParser()
            else:
                return AmexParser()
        
        return None
    
    def _save_to_excel(self, transactions: list, subdir: str):
        """Save transactions to Excel."""
        df = pd.DataFrame(transactions)
        df = df[['Name', 'Date', 'Merchant', 'Amount']]
        df = df.sort_values(['Name', 'Date'])
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(self.output_dir, f'{subdir}_{timestamp}.xlsx')
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Transactions', index=False)
            
            worksheet = writer.sheets['Transactions']
            
            for col, width in EXCEL_COLUMN_WIDTHS.items():
                col_letter = chr(65 + list(EXCEL_COLUMN_WIDTHS.keys()).index(col))
                worksheet.column_dimensions[col_letter].width = width
            
            for row in range(2, len(df) + 2):
                worksheet[f'D{row}'].number_format = '$#,##0.00'


class SimpleProgressGUI:
    """Simple progress window for PDF conversion"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PDF to Excel Converter")
        self.root.geometry("400x200")
        self.root.resizable(False, False)
        
        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - 200
        y = (self.root.winfo_screenheight() // 2) - 100
        self.root.geometry(f"+{x}+{y}")
        
        # Create widgets
        self.create_widgets()
        
        # Start conversion automatically
        self.root.after(100, self.start_conversion)
        
    def create_widgets(self):
        """Create the GUI elements"""
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title = ttk.Label(main_frame, text="Converting PDFs to Excel...", 
                         font=('Arial', 14, 'bold'))
        title.pack(pady=(0, 20))
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, length=350, mode='indeterminate')
        self.progress.pack(pady=(0, 10))
        self.progress.start(10)  # Start animation
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Checking for files...", 
                                     font=('Arial', 10))
        self.status_label.pack(pady=(0, 10))
        
        # Details label
        self.details_label = ttk.Label(main_frame, text="", 
                                      font=('Arial', 9), foreground='gray')
        self.details_label.pack()
        
    def update_status(self, message):
        """Update the status message"""
        self.status_label.config(text=message)
        self.root.update()
        
    def update_details(self, message):
        """Update the details message"""
        self.details_label.config(text=message)
        self.root.update()
        
    def start_conversion(self):
        """Start the conversion in a separate thread"""
        thread = threading.Thread(target=self.run_conversion)
        thread.daemon = True
        thread.start()
        
    def run_conversion(self):
        """Run the actual conversion"""
        try:
            # Create a custom converter that updates our GUI
            converter = GUIAwarePDFConverter(self)
            
            # Check for files
            self.update_status("Looking for PDF files...")
            pdf_count = converter._count_pdfs()
            
            if pdf_count == 0:
                self.progress.stop()
                self.update_status("No PDF files found!")
                self.update_details("Place PDFs in Convert folder and try again")
                
                # Show message and close after 5 seconds
                self.root.after(5000, self.root.quit)
                return
                
            self.update_status(f"Found {pdf_count} PDF files")
            time.sleep(1)
            
            # Run conversion
            self.update_status("Converting files...")
            converter.convert_all()
            
            # Success
            self.progress.stop()
            self.update_status("Conversion complete!")
            self.update_details("Check the Excel folder for your files")
            
            # Close after 3 seconds
            self.root.after(3000, self.root.quit)
            
        except Exception as e:
            self.progress.stop()
            self.update_status("Error occurred!")
            self.update_details(str(e))
            self.root.after(5000, self.root.quit)
    
    def run(self):
        """Start the GUI"""
        self.root.mainloop()


class GUIAwarePDFConverter(StandalonePDFConverter):
    """Modified converter that updates GUI"""
    
    def __init__(self, gui):
        super().__init__()
        self.gui = gui
        
    def convert_all(self):
        """Override to update GUI during conversion"""
        subdirs = self._get_subdirectories()
        
        for subdir in subdirs:
            subdir_path = os.path.join(self.input_dir, subdir)
            if not os.path.exists(subdir_path):
                continue
                
            pdf_files = self._find_pdf_files_in_subdir(subdir)
            if not pdf_files:
                continue
                
            self.gui.update_status(f"Processing {subdir.upper()} files...")
            
            subdir_transactions = []
            
            for i, pdf_file in enumerate(pdf_files):
                filename = os.path.basename(pdf_file)
                self.gui.update_details(f"Reading: {filename}")
                
                parser = self._get_parser_for_subdir(subdir, pdf_file)
                if not parser:
                    continue
                    
                try:
                    transactions = parser.parse_pdf(pdf_file)
                    subdir_transactions.extend(transactions)
                except Exception:
                    pass
                    
            if subdir_transactions:
                self.gui.update_details(f"Creating {subdir} Excel file...")
                self._save_to_excel(subdir_transactions, subdir)


def main():
    """Run the GUI converter"""
    app = SimpleProgressGUI()
    app.run()


if __name__ == "__main__":
    main()