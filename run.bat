@echo off
chcp 65001 >nul
title BB Death Detector

REM Check if venv exists
if not exist ".venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -r requirements/windows.txt
) else (
    call .venv\Scripts\activate.bat
)

REM Check Tesseract
where tesseract >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] Tesseract OCR not found in PATH!
    echo Download from: https://github.com/UB-Mannheim/tesseract/wiki
    echo After install, add to PATH: C:\Program Files\Tesseract-OCR
    echo.
    pause
)

echo Starting BB Death Detector...
python -m bb_detector.main

pause
