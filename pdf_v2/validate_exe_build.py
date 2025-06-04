#!/usr/bin/env python3
"""
EXE Build Validation Script
Validates that the PDF to Excel Converter exe has all required features
"""

import os
import sys
import json
import shutil
from datetime import datetime
import subprocess
import platform

class ExeBuildValidator:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'platform': platform.system(),
            'python_version': sys.version,
            'tests': []
        }
        
    def add_result(self, test_name, passed, details=""):
        """Add a test result"""
        self.results['tests'].append({
            'name': test_name,
            'passed': passed,
            'details': details
        })
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
    
    def check_source_files(self):
        """Verify all source files exist"""
        required_files = [
            'run_converter.py',
            'pdf_to_excel_converter.py',
            'requirements.txt'
        ]
        
        all_exist = True
        for file in required_files:
            exists = os.path.exists(file)
            if not exists:
                all_exist = False
            self.add_result(
                f"Source file: {file}", 
                exists,
                f"{'Found' if exists else 'Missing'} at {os.path.abspath(file)}"
            )
        
        return all_exist
    
    def check_code_features(self):
        """Verify code has all required features"""
        if not os.path.exists('run_converter.py'):
            self.add_result("Code features check", False, "run_converter.py not found")
            return False
        
        with open('run_converter.py', 'r') as f:
            content = f.read()
        
        features = {
            'W2 parsing': 'def parse_w2_pdf',
            'Validation report': 'validation_report.txt',
            'Fixed filenames': "output_file = os.path.join(self.output_dir, 'w2.xlsx')",
            'Multiple W2 forms': 'ssn_positions',
            'AmEx parsing': 'def parse_amex_pdf',
            'Chase parsing': 'def parse_chase_pdf'
        }
        
        all_found = True
        for feature, marker in features.items():
            found = marker in content
            if not found:
                all_found = False
            self.add_result(
                f"Feature: {feature}",
                found,
                f"Marker '{marker}' {'found' if found else 'not found'} in code"
            )
        
        return all_found
    
    def create_test_structure(self):
        """Create test folder structure"""
        test_dir = 'exe_test'
        
        # Clean up old test
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
        
        # Create structure
        os.makedirs(os.path.join(test_dir, 'Convert', 'amex'))
        os.makedirs(os.path.join(test_dir, 'Convert', 'chase'))
        os.makedirs(os.path.join(test_dir, 'Convert', 'w2'))
        os.makedirs(os.path.join(test_dir, 'Excel'))
        
        self.add_result(
            "Test structure created",
            True,
            f"Created test directory at {os.path.abspath(test_dir)}"
        )
        
        # Create marker files
        marker_files = [
            os.path.join(test_dir, 'Convert', 'amex', 'TEST_AMEX.pdf'),
            os.path.join(test_dir, 'Convert', 'chase', 'TEST_CHASE.pdf'),
            os.path.join(test_dir, 'Convert', 'w2', 'TEST_W2.pdf')
        ]
        
        for marker in marker_files:
            with open(marker, 'w') as f:
                f.write("This is a test marker file\n")
        
        return test_dir
    
    def check_dependencies(self):
        """Check Python dependencies"""
        try:
            import pandas
            self.add_result("pandas module", True, f"Version: {pandas.__version__}")
        except ImportError:
            self.add_result("pandas module", False, "Not installed")
        
        try:
            import pdfplumber
            self.add_result("pdfplumber module", True, f"Version: {pdfplumber.__version__}")
        except ImportError:
            self.add_result("pdfplumber module", False, "Not installed")
        
        try:
            import openpyxl
            self.add_result("openpyxl module", True, f"Version: {openpyxl.__version__}")
        except ImportError:
            self.add_result("openpyxl module", False, "Not installed")
    
    def check_pyinstaller(self):
        """Check if PyInstaller is available"""
        try:
            result = subprocess.run(['pyinstaller', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip()
                self.add_result("PyInstaller", True, f"Version: {version}")
                return True
            else:
                self.add_result("PyInstaller", False, "Command failed")
                return False
        except FileNotFoundError:
            self.add_result("PyInstaller", False, "Not installed - run: pip install pyinstaller")
            return False
    
    def test_converter_import(self):
        """Test importing the converter"""
        try:
            # Add current directory to path
            sys.path.insert(0, os.getcwd())
            
            # Try to import
            import run_converter
            
            # Check for required classes/functions
            has_converter = hasattr(run_converter, 'PDFToExcelConverter')
            
            self.add_result(
                "Import run_converter",
                has_converter,
                "PDFToExcelConverter class found" if has_converter else "Class not found"
            )
            
            return has_converter
        except Exception as e:
            self.add_result("Import run_converter", False, str(e))
            return False
    
    def save_report(self):
        """Save validation report"""
        report_file = f'exe_build_validation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📊 Validation report saved to: {report_file}")
        
        # Summary
        total_tests = len(self.results['tests'])
        passed_tests = sum(1 for t in self.results['tests'] if t['passed'])
        
        print(f"\n🎯 Summary: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("✅ All tests passed! Ready to build exe.")
            print("\n📦 To build exe, run:")
            print("   pyinstaller --onefile --name PDF_to_Excel_Converter run_converter.py")
        else:
            print("❌ Some tests failed. Please fix issues before building exe.")
            failed = [t for t in self.results['tests'] if not t['passed']]
            print("\nFailed tests:")
            for test in failed:
                print(f"  - {test['name']}: {test['details']}")
    
    def run_validation(self):
        """Run all validation checks"""
        print("🔍 PDF to Excel Converter - EXE Build Validator")
        print("=" * 50)
        
        print("\n1️⃣ Checking source files...")
        self.check_source_files()
        
        print("\n2️⃣ Checking code features...")
        self.check_code_features()
        
        print("\n3️⃣ Checking dependencies...")
        self.check_dependencies()
        
        print("\n4️⃣ Checking PyInstaller...")
        self.check_pyinstaller()
        
        print("\n5️⃣ Testing import...")
        self.test_converter_import()
        
        print("\n6️⃣ Creating test structure...")
        test_dir = self.create_test_structure()
        
        self.save_report()
        
        print(f"\n📁 Test directory created at: {os.path.abspath(test_dir)}")
        print("   You can test your exe there after building.")

if __name__ == "__main__":
    validator = ExeBuildValidator()
    validator.run_validation()