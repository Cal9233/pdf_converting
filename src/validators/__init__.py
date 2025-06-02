"""
Validators package for PDF to Excel Converter

This package contains validation logic for transaction extraction and name validation.
"""

# Import the main classes so they can be imported directly from the package
from .transaction_validator import TransactionValidator
from .name_validator import NameValidator

# Define what gets imported when someone does "from validators import *"
__all__ = [
    'TransactionValidator',
    'NameValidator'
]

# Package metadata
__version__ = '1.0.0'
__author__ = 'Your Name'