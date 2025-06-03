# run.py (at project root)
"""
PDF to Excel Converter Launcher
Handles both development and production environments with correct path resolution
"""

import sys
import os
import subprocess

def get_application_path():
    """Get the correct path whether running as script or exe"""
    if getattr(sys, 'frozen', False):
        # Running as exe (PyInstaller)
        return os.path.dirname(sys.executable)
    else:
        # Running as script - return project root (where run.py is located)
        return os.path.dirname(os.path.abspath(__file__))

def setup_paths():
    """Setup all necessary paths for the application"""
    # Get the application base path
    app_path = get_application_path()
    
    # Ensure we're working from the correct directory
    os.chdir(app_path)
    
    # Add paths for imports
    project_root = app_path
    src_path = os.path.join(project_root, 'src')
    
    # Add both to Python path
    sys.path.insert(0, project_root)
    sys.path.insert(0, src_path)
    
    return app_path, project_root, src_path

def main():
    try:
        print("🚀 PDF to Excel Converter - Starting...")
        
        # Setup paths first
        app_path, project_root, src_path = setup_paths()
        
        print(f"📁 Application path: {app_path}")
        print(f"📁 Project root: {project_root}")
        print(f"📁 Source path: {src_path}")
        
        # Verify folder structure
        convert_folder = os.path.join(app_path, 'Convert')
        excel_folder = os.path.join(app_path, 'Excel')
        
        print(f"📁 Convert folder: {convert_folder}")
        print(f"📁 Excel folder: {excel_folder}")
        
        # Create folders if they don't exist
        os.makedirs(convert_folder, exist_ok=True)
        os.makedirs(excel_folder, exist_ok=True)
        
        # Import and run the converter directly
        try:
            print("🔄 Importing converter...")
            
            # Try different import paths depending on environment
            if getattr(sys, 'frozen', False):
                # Running as executable - try direct import
                from src import UniversalPDFToExcelConverter
                print("✅ Successfully imported from src package")
            else:
                # Running as script - use main module
                try:
                    from src.main import main as src_main
                    print("✅ Successfully imported from src.main")
                    result = src_main()
                    print(f"✅ Conversion completed with result: {result}")
                    return
                except ImportError:
                    # Fallback to direct converter import
                    from src import UniversalPDFToExcelConverter
                    print("✅ Successfully imported converter class")
            
            # Run the converter
            print("🔄 Starting conversion process...")
            
            # Import UI components
            from src.ui import show_completion_message_with_validation
            
            # Create converter and run
            converter = UniversalPDFToExcelConverter()
            
            # Show progress window and run conversion
            progress_window = converter.progress_window.show_progress_window()
            
            try:
                if progress_window:
                    files_created, total_transactions = converter.run()
                else:
                    print("⚠️  GUI not available, running in console mode...")
                    files_created, total_transactions = converter.run()
                    
            except Exception as e:
                converter.progress_window.update_progress("❌ Critical error", f"Error: {str(e)}")
                print(f"❌ Critical error during conversion: {str(e)}")
                files_created, total_transactions = 0, 0
            
            # Close progress window
            converter.progress_window.close_progress_window()
            
            # Show completion message
            show_completion_message_with_validation(converter, files_created, total_transactions)
            
            # Console summary
            print("\n" + "=" * 50)
            print("🎉 CONVERSION COMPLETE!")
            print(f"📊 Results: {files_created} Excel files created, {total_transactions} transactions processed")
            print("=" * 50)
            
        except ImportError as e:
            print(f"❌ Import error: {e}")
            print("💡 Available modules:")
            print(f"   sys.path: {sys.path[:3]}...")
            
            # Try to find what's actually available
            try:
                import pkgutil
                print("   Available packages:")
                for importer, modname, ispkg in pkgutil.iter_modules():
                    if 'src' in modname or 'config' in modname:
                        print(f"     {modname} ({'package' if ispkg else 'module'})")
            except:
                pass
            
            return False
                
    except Exception as e:
        print(f"💥 Error: {e}")
        print("\n🔍 Debug info:")
        print(f"   Frozen: {getattr(sys, 'frozen', False)}")
        print(f"   Executable: {sys.executable}")
        print(f"   App path: {get_application_path()}")
        print(f"   Current working directory: {os.getcwd()}")
        print(f"   Python path: {sys.path[:3]}...")
        
        try:
            print(f"   Files in current directory: {os.listdir('.')}")
            if os.path.exists('src'):
                print(f"   Files in src: {os.listdir('src')}")
        except Exception:
            print("   Could not list directory contents")
            
        input("Press Enter to exit...")
        return False

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Conversion cancelled by user")
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        input("Press Enter to exit...")