"""
Configuration settings for PDF to Excel Converter

This module contains all configuration constants and settings used throughout
the application. Modify these values to customize the application behavior.
"""

import os
import sys
from pathlib import Path

# =============================================================================
# PATH RESOLUTION FUNCTIONS
# =============================================================================

def get_application_root():
    """
    Get the application root directory - works for both development and executable.
    
    Returns:
        Path: The root directory where Convert/Excel folders should be located
    """
    if getattr(sys, 'frozen', False):
        # Running as executable (PyInstaller)
        # Return the directory containing the executable
        return Path(os.path.dirname(sys.executable))
    else:
        # Running as script in development
        # We're in config/settings.py, need to go up 2 levels to project root
        current_file = Path(__file__).resolve()
        return current_file.parent.parent  # config/ -> project_root/

# =============================================================================
# FOLDER SETTINGS
# =============================================================================

# Default folder names (relative)
DEFAULT_CONVERT_FOLDER = "Convert"
DEFAULT_EXCEL_FOLDER = "Excel"
DEFAULT_LOGS_FOLDER = "logs"

# File patterns
PDF_EXTENSIONS = ['.pdf']
EXCEL_EXTENSION = '.xlsx'

# =============================================================================
# VALIDATION SETTINGS
# =============================================================================

# Confidence score thresholds
CONFIDENCE_EXCELLENT = 95  # 95%+ = Excellent
CONFIDENCE_GOOD = 85       # 85-94% = Good
CONFIDENCE_NEEDS_REVIEW = 85  # <85% = Needs Review

# Validation penalties
MAX_EXTRACTION_PENALTY = 50  # Max penalty for low extraction ratio
MAX_MISSED_PENALTY = 30      # Max penalty for missed transactions
MAX_AMOUNT_PENALTY = 25      # Max penalty for amount discrepancies

# Missed transaction penalty (per transaction)
MISSED_TRANSACTION_PENALTY = 5

# =============================================================================
# PARSER SETTINGS
# =============================================================================

# AmEx Settings
AMEX_KEYWORDS = [
    'AMERICAN EXPRESS',
    'AMAZON BUSINESS PRIME CARD',
    'AMEX'
]

# Chase Settings
CHASE_KEYWORDS = [
    'CHASE',
    'ULTIMATE REWARDS',
    'ACCOUNT ACTIVITY'
]

# Date handling
TWO_DIGIT_YEAR_CUTOFF = 50  # Years >= 50 = 19xx, < 50 = 20xx

# =============================================================================
# NAME VALIDATION SETTINGS
# =============================================================================

# Valid name parts for cardholder names
VALID_NAME_PARTS = ['JR', 'SR', 'III', 'IV', 'II', 'DE', 'LA', 'DEL', 'VON', 'VAN', 'MC', 'MAC']

# Business terms to exclude from names
BUSINESS_TERMS = [
    'STN', 'LLC', 'INC', 'CORP', 'LTD', 'CO', 'STORE', 'SHOP',
    'MARKET', 'CENTER', 'DEPOT', 'STATION', 'FUEL', 'GAS', 'OIL'
]

# AmEx false positives
AMEX_FALSE_POSITIVES = [
    'ACCOUNT ENDING', 'CARD ENDING', 'CUSTOMER CARE', 'AMAZON BUSINESS',
    'AMERICAN EXPRESS', 'PAYMENT TERMS', 'NEW CHARGES', 'TOTAL BALANCE',
    'MINIMUM PAYMENT', 'INTEREST CHARGED', 'DETAIL CONTINUED', 'AMOUNT ENCLOSED',
    'SERVICE STN', 'FAST FOOD', 'RESTAURANT', 'GAS STATION', 'AUTO PAY',
    'GROCERY OUTLET', 'UNION', 'CHEVRON', 'SHELL OIL', 'MOBILE', 'ARCO',
    'SAFEWAY', 'COSTCO', 'TARGET', 'WALMART', 'HOME DEPOT'
]

# Chase false positives
CHASE_FALSE_POSITIVES = [
    'ACCOUNT SUMMARY', 'ACCOUNT ACTIVITY', 'ACCOUNT MESSAGES', 'ACCOUNT NUMBER',
    'CHASE ULTIMATE', 'ULTIMATE REWARDS', 'CUSTOMER SERVICE', 'PAYMENT DUE',
    'NEW BALANCE', 'MINIMUM PAYMENT', 'TRANSACTIONS THIS', 'INCLUDING PAYMENTS',
    'PREVIOUS BALANCE', 'CASH ADVANCES', 'BALANCE TRANSFERS', 'INTEREST CHARGED',
    'LATE PAYMENT', 'OVERLIMIT FEE', 'ANNUAL FEE', 'FINANCE CHARGE',
    'SERVICE STATION', 'GAS STATION', 'GROCERY STORE', 'DEPARTMENT STORE',
    'FAST FOOD', 'RESTAURANT', 'COFFEE SHOP', 'AUTO PARTS', 'HOME DEPOT'
]

# =============================================================================
# UI SETTINGS
# =============================================================================

# Progress window settings
PROGRESS_WINDOW_WIDTH = 350
PROGRESS_WINDOW_HEIGHT = 150
PROGRESS_UPDATE_INTERVAL = 0.3  # seconds

# Progress bar settings
PROGRESS_BAR_SPEED = 10  # milliseconds

# =============================================================================
# EXCEL EXPORT SETTINGS
# =============================================================================

# Column order for Excel output
EXCEL_COLUMN_ORDER = ['Name', 'Date', 'Merchant', 'Amount']

# Column width settings
MAX_COLUMN_WIDTH = 50
COLUMN_WIDTH_PADDING = 2

# Filename timestamp format
TIMESTAMP_FORMAT = '%Y%m%d_%H%M%S'

# =============================================================================
# LOGGING SETTINGS
# =============================================================================

# Log levels
LOG_LEVEL_DEBUG = 'DEBUG'
LOG_LEVEL_INFO = 'INFO'
LOG_LEVEL_WARNING = 'WARNING'
LOG_LEVEL_ERROR = 'ERROR'

# Default log level
DEFAULT_LOG_LEVEL = LOG_LEVEL_INFO

# =============================================================================
# APPLICATION METADATA
# =============================================================================

APP_NAME = "PDF to Excel Converter"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Convert PDF credit card statements to Excel format"

# =============================================================================
# FILE PATHS (Computed at runtime)
# =============================================================================

# Get application root directory (works for both development and executable)
try:
    PROJECT_ROOT = get_application_root()
    CONVERT_FOLDER_PATH = PROJECT_ROOT / DEFAULT_CONVERT_FOLDER
    EXCEL_FOLDER_PATH = PROJECT_ROOT / DEFAULT_EXCEL_FOLDER
    LOGS_FOLDER_PATH = PROJECT_ROOT / DEFAULT_LOGS_FOLDER
    
    # Debug information (can be removed in production)
    print(f"📁 Config initialized:")
    print(f"   Project root: {PROJECT_ROOT}")
    print(f"   Convert path: {CONVERT_FOLDER_PATH}")
    print(f"   Excel path: {EXCEL_FOLDER_PATH}")
    print(f"   Logs path: {LOGS_FOLDER_PATH}")
    print(f"   Running as exe: {getattr(sys, 'frozen', False)}")
    
except Exception as e:
    # Fallback to current directory if something goes wrong
    print(f"⚠️  Warning: Could not determine project root ({e}), using current directory")
    PROJECT_ROOT = Path.cwd()
    CONVERT_FOLDER_PATH = PROJECT_ROOT / DEFAULT_CONVERT_FOLDER
    EXCEL_FOLDER_PATH = PROJECT_ROOT / DEFAULT_EXCEL_FOLDER
    LOGS_FOLDER_PATH = PROJECT_ROOT / DEFAULT_LOGS_FOLDER

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_convert_folder():
    """Get the absolute path to the Convert folder"""
    return str(CONVERT_FOLDER_PATH)

def get_excel_folder():
    """Get the absolute path to the Excel folder"""
    return str(EXCEL_FOLDER_PATH)

def get_logs_folder():
    """Get the absolute path to the logs folder"""
    return str(LOGS_FOLDER_PATH)

def get_project_root():
    """Get the absolute path to the project root"""
    return str(PROJECT_ROOT)

def debug_paths():
    """Print debug information about all configured paths"""
    print("\n🔍 Configuration Debug Info:")
    print(f"   Running as executable: {getattr(sys, 'frozen', False)}")
    print(f"   Config file location: {__file__}")
    print(f"   Project root: {PROJECT_ROOT}")
    print(f"   Convert folder: {CONVERT_FOLDER_PATH}")
    print(f"   Excel folder: {EXCEL_FOLDER_PATH}")
    print(f"   Logs folder: {LOGS_FOLDER_PATH}")
    print(f"   Current working directory: {Path.cwd()}")
    
    # Check if folders exist
    print(f"   Convert exists: {CONVERT_FOLDER_PATH.exists()}")
    print(f"   Excel exists: {EXCEL_FOLDER_PATH.exists()}")
    print(f"   Logs exists: {LOGS_FOLDER_PATH.exists()}")
    print()