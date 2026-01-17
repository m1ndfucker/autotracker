@echo off
chcp 65001 >nul
title Building BB Death Detector

REM Activate venv
if not exist ".venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv .venv
)
call .venv\Scripts\activate.bat

REM Install build dependencies
echo Installing build dependencies...
pip install pyinstaller -q

REM Clean previous builds
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

echo.
echo Building BB Death Detector...
echo.

pyinstaller ^
    --name "BB Death Detector" ^
    --onefile ^
    --windowed ^
    --icon "assets/icon.ico" ^
    --add-data "assets;assets" ^
    --hidden-import "pynput.keyboard._win32" ^
    --hidden-import "pynput.mouse._win32" ^
    --hidden-import "PIL._tkinter_finder" ^
    --hidden-import "websockets" ^
    --collect-all "dearpygui" ^
    bb_detector/main.py

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo Build successful!
    echo EXE location: dist\BB Death Detector.exe
    echo ========================================
    echo.
    echo NOTE: Users still need Tesseract OCR installed:
    echo https://github.com/UB-Mannheim/tesseract/wiki
) else (
    echo.
    echo Build failed!
)

pause
