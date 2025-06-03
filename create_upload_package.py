#!/usr/bin/env python3
"""
Create Clean Upload Package Script
Creates a minimal package with only essential files for deployment
"""

import os
import shutil
import sys
from pathlib import Path

def create_clean_upload_package():
    """Create a clean package with only essential files"""
    
    print("📦 Creating clean upload package...")
    
    # Define package name
    package_name = "pdf_converter_upload"
    
    # Clean existing package
    if os.path.exists(package_name):
        shutil.rmtree(package_name)
        print(f"🧹 Cleaned existing {package_name}")
    
    # Create package directory
    os.makedirs(package_name)
    print(f"📁 Created {package_name} directory")
    
    # Essential files to copy
    essential_files = [
        'run.py',
        'build.py', 
        'README.md'
    ]
    
    # Essential directories to copy
    essential_dirs = [
        'src',
        'config'
    ]
    
    # Working directories to create (empty)
    working_dirs = [
        'Convert',
        'Excel', 
        'logs'
    ]
    
    # Copy essential files
    for file_name in essential_files:
        if os.path.exists(file_name):
            shutil.copy2(file_name, os.path.join(package_name, file_name))
            print(f"✅ Copied {file_name}")
        else:
            print(f"⚠️  {file_name} not found - skipping")
    
    # Copy essential directories
    for dir_name in essential_dirs:
        if os.path.exists(dir_name):
            dest_dir = os.path.join(package_name, dir_name)
            shutil.copytree(dir_name, dest_dir, ignore=ignore_cache_files)
            print(f"✅ Copied {dir_name}/ directory")
        else:
            print(f"⚠️  {dir_name}/ not found - skipping")
    
    # Create working directories
    for dir_name in working_dirs:
        dir_path = os.path.join(package_name, dir_name)
        os.makedirs(dir_path, exist_ok=True)
        
        # Add .gitkeep to preserve empty directories
        gitkeep_path = os.path.join(dir_path, '.gitkeep')
        with open(gitkeep_path, 'w') as f:
            f.write('')
        print(f"✅ Created {dir_name}/ directory")
    
    # Create requirements.txt
    create_requirements_file(package_name)
    
    # Copy launch instructions
    copy_launch_instructions(package_name)
    
    # Create deployment script
    create_deployment_script(package_name)
    
    # Show package contents
    show_package_contents(package_name)
    
    # Create zip file
    create_zip_package(package_name)
    
    print(f"\n🎉 Clean upload package created!")
    print(f"📁 Package location: {package_name}/")
    print(f"📦 Zip file: {package_name}.zip")
    print(f"\n📋 Ready for upload to cloud server!")

def ignore_cache_files(dir, files):
    """Ignore function for shutil.copytree to skip cache files"""
    ignore_patterns = {
        '__pycache__',
        '*.pyc',
        '*.pyo',
        '*.pyd',
        '.DS_Store',
        '.pytest_cache',
        '.coverage'
    }
    
    ignored = []
    for file in files:
        if file in ignore_patterns or any(file.endswith(pattern.replace('*', '')) for pattern in ignore_patterns if '*' in pattern):
            ignored.append(file)
    
    return ignored

def create_requirements_file(package_name):
    """Create requirements.txt with essential dependencies"""
    requirements_content = """# PDF to Excel Converter Dependencies

# Core PDF processing
pdfplumber>=0.11.0

# Data manipulation and Excel export
pandas>=2.0.0
openpyxl>=3.1.0

# Build tool (optional - only needed for creating executables)
pyinstaller>=6.0.0

# Standard library modules (included with Python)
# tkinter - GUI components
# pathlib - Path handling
# datetime - Date/time utilities
# re - Regular expressions
"""
    
    requirements_path = os.path.join(package_name, 'requirements.txt')
    with open(requirements_path, 'w') as f:
        f.write(requirements_content)
    print("✅ Created requirements.txt")

def copy_launch_instructions(package_name):
    """Copy or create launch instructions"""
    instructions_source = "LAUNCH_INSTRUCTIONS.md"
    instructions_dest = os.path.join(package_name, "LAUNCH_INSTRUCTIONS.md")
    
    if os.path.exists(instructions_source):
        shutil.copy2(instructions_source, instructions_dest)
        print("✅ Copied LAUNCH_INSTRUCTIONS.md")
    else:
        # Create basic instructions if file doesn't exist
        basic_instructions = """# Quick Launch Instructions

## Setup:
1. `python3 -m venv venv`
2. `source venv/bin/activate`
3. `pip install -r requirements.txt`

## Run:
4. `python run.py`

## Build:
5. `python build.py`

See full documentation in README.md
"""
        with open(instructions_dest, 'w') as f:
            f.write(basic_instructions)
        print("✅ Created basic LAUNCH_INSTRUCTIONS.md")

def create_deployment_script(package_name):
    """Create deployment script for easy server setup"""
    deploy_script = """#!/bin/bash
# deploy.sh - Easy deployment script

echo "🚀 PDF Converter Deployment Script"
echo "=================================="

# Check Python version
echo "📋 Checking Python..."
python3 --version

# Create virtual environment
echo "🔧 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "⚡ Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Test installation
echo "🧪 Testing installation..."
python -c "import pdfplumber, pandas, openpyxl; print('✅ All dependencies installed!')"

# Test application
echo "🏃 Testing application..."
echo "Ready to run: python run.py"
echo "Ready to build: python build.py"

echo ""
echo "🎉 Deployment complete!"
echo "Run the app with: python run.py"
"""
    
    deploy_path = os.path.join(package_name, 'deploy.sh')
    with open(deploy_path, 'w') as f:
        f.write(deploy_script)
    
    # Make executable on Unix systems
    try:
        os.chmod(deploy_path, 0o755)
    except:
        pass  # Windows doesn't need this
    
    print("✅ Created deploy.sh")

def show_package_contents(package_name):
    """Show the contents of the created package"""
    print(f"\n📁 Package contents ({package_name}/):")
    
    def show_tree(directory, prefix="", max_depth=3, current_depth=0):
        if current_depth >= max_depth:
            return
            
        items = sorted(os.listdir(directory))
        for i, item in enumerate(items):
            path = os.path.join(directory, item)
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "
            
            if os.path.isdir(path):
                print(f"{prefix}{current_prefix}{item}/")
                next_prefix = prefix + ("    " if is_last else "│   ")
                show_tree(path, next_prefix, max_depth, current_depth + 1)
            else:
                size = os.path.getsize(path)
                if size > 1024:
                    size_str = f" ({size // 1024}KB)"
                else:
                    size_str = f" ({size}B)"
                print(f"{prefix}{current_prefix}{item}{size_str}")
    
    show_tree(package_name)

def create_zip_package(package_name):
    """Create a zip file of the package"""
    import zipfile
    
    zip_name = f"{package_name}.zip"
    
    # Remove existing zip
    if os.path.exists(zip_name):
        os.remove(zip_name)
    
    # Create new zip
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_name):
            for file in files:
                file_path = os.path.join(root, file)
                arc_name = os.path.relpath(file_path, package_name)
                zipf.write(file_path, arc_name)
    
    zip_size = os.path.getsize(zip_name)
    if zip_size > 1024 * 1024:
        size_str = f"{zip_size / (1024 * 1024):.1f}MB"
    else:
        size_str = f"{zip_size / 1024:.1f}KB"
    
    print(f"✅ Created {zip_name} ({size_str})")

def get_package_stats(package_name):
    """Get statistics about the package"""
    total_files = 0
    total_size = 0
    
    for root, dirs, files in os.walk(package_name):
        total_files += len(files)
        for file in files:
            file_path = os.path.join(root, file)
            total_size += os.path.getsize(file_path)
    
    return total_files, total_size

if __name__ == "__main__":
    try:
        create_clean_upload_package()
    except Exception as e:
        print(f"❌ Error creating package: {e}")
        sys.exit(1)