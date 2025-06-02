"""
PDF to Excel Converter - Main Entry Point

This is the main entry point for the PDF to Excel converter application.
It orchestrates the entire conversion process using the refactored component architecture.

Usage:
    python src/main.py

The application will:
1. Show a progress window
2. Process all PDFs in the 'Convert' folder
3. Create Excel files in the 'Excel' folder
4. Generate validation reports
5. Show completion dialog with results
"""

import sys
import os

# Add the project root to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import UniversalPDFToExcelConverter
from src.ui import show_completion_message_with_validation


def main():
    """Main entry point for the PDF to Excel conversion process"""
    print("🏦 PDF to Excel Converter Starting...")
    print("=" * 50)
    
    try:
        # Create the converter instance
        converter = UniversalPDFToExcelConverter()
        
        # Show progress window
        progress_window = converter.progress_window.show_progress_window()
        
        files_created = 0
        total_transactions = 0
        
        try:
            if progress_window:
                # Run conversion with progress window
                files_created, total_transactions = converter.run()
            else:
                # Fallback: run without GUI (console mode)
                print("⚠️  GUI not available, running in console mode...")
                files_created, total_transactions = converter.run()
                
        except Exception as e:
            converter.progress_window.update_progress("❌ Critical error", f"Error: {str(e)}")
            print(f"❌ Critical error during conversion: {str(e)}")
        
        # Close progress window
        converter.progress_window.close_progress_window()
        
        # Show completion message with validation info
        show_completion_message_with_validation(converter, files_created, total_transactions)
        
        # Console summary
        print("\n" + "=" * 50)
        print("🎉 CONVERSION COMPLETE!")
        print(f"📊 Results: {files_created} Excel files created, {total_transactions} transactions processed")
        
        if hasattr(converter, 'validator') and converter.validator.validation_results:
            total_files = len(converter.validator.validation_results)
            high_confidence = sum(1 for r in converter.validator.validation_results.values() if r['confidence_score'] >= 95)
            print(f"📋 Validation: {high_confidence}/{total_files} files with high confidence (95%+)")
        
        print("✅ Check the 'Excel' folder for your results!")
        print("=" * 50)
        
        return files_created, total_transactions
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("💡 Make sure all required packages are installed:")
        print("   pip install pandas openpyxl pdfplumber")
        return 0, 0
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("💡 Please check that your project structure is correct")
        return 0, 0


if __name__ == "__main__":
    try:
        main()
        input("\nPress Enter to exit...")  # Keep console open to see results
    except KeyboardInterrupt:
        print("\n🛑 Conversion cancelled by user")
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        input("Press Enter to exit...")