@echo off
chcp 65001 >nul
title Building BB Death Detector (Full Bundle)

echo ============================================
echo BB Death Detector - Full Build Script
echo ============================================
echo.

REM Activate venv
if not exist ".venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv .venv
)
call .venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements/windows.txt -q
pip install pyinstaller -q

REM Prepare Tesseract if not ready
if not exist "assets\tesseract\tesseract.exe" (
    echo.
    echo Preparing Tesseract...
    call scripts\prepare_tesseract.bat
)

REM Verify Tesseract is ready
if not exist "assets\tesseract\tesseract.exe" (
    echo.
    echo [WARNING] Tesseract not bundled!
    echo Users will need to install Tesseract separately.
    echo.
    choice /C YN /M "Continue anyway?"
    if errorlevel 2 exit /b 1
)

REM Clean previous builds
echo.
echo Cleaning previous builds...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

REM Build
echo.
echo Building executable...
echo.

pyinstaller bb_detector.spec

if %errorlevel% equ 0 (
    echo.
    echo ============================================
    echo BUILD SUCCESSFUL!
    echo ============================================
    echo.
    echo Output: dist\BB Death Detector.exe
    echo.
    if exist "assets\tesseract\tesseract.exe" (
        echo Tesseract: BUNDLED - No installation required!
    ) else (
        echo Tesseract: NOT BUNDLED
    )
    echo.

    REM Show file size
    for %%A in ("dist\BB Death Detector.exe") do echo Size: %%~zA bytes
    echo.
) else (
    echo.
    echo BUILD FAILED!
    echo.
)

pause
