# -*- mode: python ; coding: utf-8 -*-

import os

# Collect all data files
datas = []

# Add all Python files from src directory
src_path = os.path.join(os.getcwd(), 'src')
if os.path.exists(src_path):
    for root, dirs, files in os.walk(src_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, os.getcwd())
                dest_path = os.path.dirname(rel_path)
                datas.append((file_path, dest_path))

# Add config package (including __init__.py)
config_path = os.path.join(os.getcwd(), 'config')
if os.path.exists(config_path):
    for file in os.listdir(config_path):
        if file.endswith('.py'):
            file_path = os.path.join(config_path, file)
            datas.append((file_path, 'config'))
            print(f"Including config file: {file}")

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'pdfplumber',
        'pandas', 
        'openpyxl',
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'config',
        'config.settings',
        'src.core.converter',
        'src.core.folder_manager',
        'src.parsers.amex_parser',
        'src.parsers.chase_parser',
        'src.parsers.base_parser',
        'src.validators.transaction_validator',
        'src.validators.name_validator',
        'src.exporters.excel_exporter',
        'src.ui.progress_window',
        'src.ui.completion_dialog',
        'src.utils.date_utils',
        'src.utils.file_utils',
        'src.utils.text_utils'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PDF_to_Excel_Converter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Change to False to hide console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
