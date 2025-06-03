import os

class FileUtils:
    """Utility functions for file operations"""
    
    @staticmethod
    def ensure_directory_exists(directory_path):
        """Create directory if it doesn't exist"""
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
            return True
        return False
    
    @staticmethod
    def get_file_extension(filepath):
        """Get file extension from filepath"""
        return os.path.splitext(filepath)[1].lower()
    
    @staticmethod
    def is_pdf_file(filepath):
        """Check if file is a PDF"""
        return FileUtils.get_file_extension(filepath) == '.pdf'