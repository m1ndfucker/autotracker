# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for BB Death Detector.

Build command:
    pyinstaller bb_detector.spec
"""

import sys
from pathlib import Path

block_cipher = None

# Paths
ROOT = Path(SPECPATH)
ASSETS = ROOT / 'assets'
TESSERACT = ASSETS / 'tesseract'

# Collect tesseract binaries if they exist
tesseract_binaries = []
tesseract_datas = []
if TESSERACT.exists():
    # Add tesseract.exe and DLLs as binaries
    for ext in ['*.exe', '*.dll']:
        for f in TESSERACT.glob(ext):
            tesseract_binaries.append((str(f), 'assets/tesseract'))
    # Add tessdata as data
    tessdata = TESSERACT / 'tessdata'
    if tessdata.exists():
        tesseract_datas.append((str(tessdata), 'assets/tesseract/tessdata'))

a = Analysis(
    ['bb_detector/main.py'],
    pathex=[str(ROOT)],
    binaries=tesseract_binaries,
    datas=[
        (str(ASSETS), 'assets'),
    ] + tesseract_datas,
    hiddenimports=[
        # pynput backends
        'pynput.keyboard._win32',
        'pynput.mouse._win32',
        # PIL
        'PIL._tkinter_finder',
        # websockets
        'websockets',
        'websockets.legacy',
        'websockets.legacy.client',
        # dearpygui
        'dearpygui',
        'dearpygui.dearpygui',
        # win32
        'win32gui',
        'win32process',
        'win32api',
        'win32con',
        # mss
        'mss',
        'mss.windows',
        # bettercam (optional)
        'bettercam',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude macOS-only packages
        'pyobjc',
        'pyobjc-core',
        'pyobjc-framework-Cocoa',
        'pyobjc-framework-Quartz',
        'pyobjc-framework-CoreText',
        'pyobjc-framework-ApplicationServices',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='BB Death Detector',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if (ASSETS / 'icon.ico').exists() else None,
)
