#!/usr/bin/env python3
"""
Path Comparison Script
Shows the difference between old and new path handling
"""

import os
import sys

print("🔍 Path Handling Comparison")
print("="*50)

# Check if running as frozen exe
is_frozen = getattr(sys, 'frozen', False)
print(f"\nRunning as EXE: {is_frozen}")
print(f"Current working directory: {os.getcwd()}")
print(f"sys.executable: {sys.executable}")

if is_frozen:
    print("\n[EXE Mode]")
else:
    print("\n[Script Mode]")
    print(f"Script file: {__file__}")
    print(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")

print("\n📁 Original Program Method (works):")
print("  self.convert_folder = 'Convert'")
print("  self.excel_folder = 'Excel'")
print(f"  → Convert path: {os.path.abspath('Convert')}")
print(f"  → Excel path: {os.path.abspath('Excel')}")

print("\n❌ Previous Method (doesn't work with custom folder):")
if is_frozen:
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))
print(f"  base_dir = {base_dir}")
print(f"  → Convert path: {os.path.join(base_dir, 'Convert')}")
print(f"  → Excel path: {os.path.join(base_dir, 'Excel')}")

print("\n✅ Fixed Method (works like original):")
print("  self.input_dir = 'Convert'")
print("  self.output_dir = 'Excel'")
print(f"  → Convert path: {os.path.abspath('Convert')}")
print(f"  → Excel path: {os.path.abspath('Excel')}")

print("\n💡 Summary:")
print("The original works because it uses relative paths from the")
print("current working directory, not the executable's directory.")
print("\nWhen you place the exe in your custom folder and run it,")
print("it looks for Convert/Excel folders in that same folder.")

input("\nPress Enter to exit...")