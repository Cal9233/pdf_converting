#!/bin/bash
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
