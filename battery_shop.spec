# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_all

block_cipher = None


pandas_datas, pandas_binaries, pandas_hiddenimports = collect_all('pandas')
openpyxl_datas, openpyxl_binaries, openpyxl_hiddenimports = collect_all('openpyxl')

a = Analysis(
    ['main.py'],
    pathex=[os.path.abspath('.')],  # ensures PyInstaller sees your local modules
    binaries=(
        pandas_binaries +
        openpyxl_binaries
    ),
    datas=[
        ('logo.ico', '.'),          # your icon
        ('.env', '.'),              # environment file
        ('Amaron-Logo.png', '.'), 
        *pandas_datas,              # every pandas data file, extension, etc.
        *openpyxl_datas             # every openpyxl data file, extension, etc.
    ],
    hiddenimports=[
        'pymongo',
        'pandas',
        'openpyxl',        
        'python-dotenv',
        'PyQt5',
        'PyQt5.QtPrintSupport',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        *pandas_hiddenimports,
        *openpyxl_hiddenimports
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Battery Shop',  # your .exe name
    onefile=True,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                   # False = no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='logo.ico'
)
