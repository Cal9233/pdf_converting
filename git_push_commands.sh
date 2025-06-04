#!/bin/bash
# Git commands to push the cleaned up project to main branch

# First, add all the new files
git add BUILD.bat
git add pdf_usb/
git add pdf_v2/
git add README.md

# Remove all the deleted files from git
git add -u

# Create a comprehensive commit
git commit -m "Major refactor: Clean GUI version with progress bar

- Removed all old converter versions and redundant code
- Created clean pdf_v2/ with GUI progress bar
- Set up pdf_usb/ for easy distribution
- Simplified build process with single BUILD.bat
- Updated documentation
- Removed Docker files and old configurations
- Clean merchant name extraction
- Automatic PDF detection by bank type"

# Push to main branch
git push origin main

echo "Push complete!"