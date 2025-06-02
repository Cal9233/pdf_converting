"""
Completion dialog functions for PDF to Excel Converter

This module provides completion message dialogs for the conversion process.
"""

import tkinter as tk
from tkinter import messagebox


def show_completion_message(files_created, total_transactions):
    """Show completion message using GUI"""
    try:
        # Create a hidden root window
        root = tk.Tk()
        root.withdraw()
        
        # Show completion message
        if files_created > 0:
            message = f"✅ SUCCESS!\n\n" \
                     f"Created {files_created} Excel file(s)\n" \
                     f"Processed {total_transactions} transactions\n\n" \
                     f"Check the 'Excel' folder for your results!"
            title = "PDF to Excel Conversion - Complete"
        else:
            message = "⚠️ No Excel files were created.\n\n" \
                     "Please check that your PDFs contain transaction data\n" \
                     "and try again."
            title = "PDF to Excel Conversion - No Data Found"
        
        messagebox.showinfo(title, message)
        root.destroy()
        
    except Exception:
        # Fallback: console message
        try:
            if files_created > 0:
                print(f"✅ SUCCESS! Created {files_created} Excel file(s), Processed {total_transactions} transactions")
            else:
                print("⚠️ No Excel files were created.")
        except Exception:
            pass


def show_completion_message_with_validation(converter, files_created, total_transactions):
    """Enhanced completion message that includes validation summary"""
    try:
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