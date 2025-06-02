"""
Configuration package for PDF to Excel Converter

This package contains all configuration settings, constants, and application metadata.
Import settings from this package to access configuration values throughout the application.
"""

from .settings import *

# Make commonly used settings easily accessible
__all__ = [
    # Folder settings
    'DEFAULT_CONVERT_FOLDER',
    'DEFAULT_EXCEL_FOLDER',
    'DEFAULT_LOGS_FOLDER',
    
    # Validation settings
    'CONFIDENCE_EXCELLENT',
    'CONFIDENCE_GOOD',
    'CONFIDENCE_NEEDS_REVIEW',
    
    # Parser settings
    'AMEX_KEYWORDS',
    'CHASE_KEYWORDS',
    'TWO_DIGIT_YEAR_CUTOFF',
    
    # Name validation
    'VALID_NAME_PARTS',
    'BUSINESS_TERMS',
    'AMEX_FALSE_POSITIVES',
    'CHASE_FALSE_POSITIVES',
    
    # Excel settings
    'EXCEL_COLUMN_ORDER',
    'TIMESTAMP_FORMAT',
    
    # App metadata
    'APP_NAME',
    'APP_VERSION',
    'APP_DESCRIPTION',
    
    # Computed paths
    'PROJECT_ROOT',
    'CONVERT_FOLDER_PATH',
    'EXCEL_FOLDER_PATH',
    'LOGS_FOLDER_PATH'
]

__version__ = '1.0.0'