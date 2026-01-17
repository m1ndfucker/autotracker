@echo off
chcp 65001 >nul
title Prepare Tesseract for Bundle

echo ============================================
echo Prepare Tesseract for bundling
echo ============================================
echo.

set TESSERACT_DIR=assets\tesseract
set TESSDATA_DIR=%TESSERACT_DIR%\tessdata

REM Check if already prepared
if exist "%TESSERACT_DIR%\tesseract.exe" (
    echo [OK] Tesseract already prepared in %TESSERACT_DIR%
    goto :check_tessdata
)

REM Try to find installed Tesseract
echo Looking for installed Tesseract...

set FOUND=0

if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    set SOURCE=C:\Program Files\Tesseract-OCR
    set FOUND=1
)

if exist "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe" (
    set SOURCE=C:\Program Files (x86)\Tesseract-OCR
    set FOUND=1
)

if %FOUND%==0 (
    echo.
    echo [ERROR] Tesseract not found!
    echo.
    echo Please install Tesseract first:
    echo   https://github.com/UB-Mannheim/tesseract/wiki
    echo.
    echo Then run this script again.
    pause
    exit /b 1
)

echo Found: %SOURCE%
echo.

REM Create directories
if not exist "%TESSERACT_DIR%" mkdir "%TESSERACT_DIR%"
if not exist "%TESSDATA_DIR%" mkdir "%TESSDATA_DIR%"

REM Copy files
echo Copying Tesseract files...

copy "%SOURCE%\tesseract.exe" "%TESSERACT_DIR%\" >nul
if errorlevel 1 (
    echo [ERROR] Failed to copy tesseract.exe
    pause
    exit /b 1
)

echo   Copied tesseract.exe

REM Copy all DLLs
for %%f in ("%SOURCE%\*.dll") do (
    copy "%%f" "%TESSERACT_DIR%\" >nul
    echo   Copied %%~nxf
)

:check_tessdata
REM Copy tessdata
echo.
echo Copying tessdata...

if exist "%SOURCE%\tessdata\eng.traineddata" (
    copy "%SOURCE%\tessdata\eng.traineddata" "%TESSDATA_DIR%\" >nul
    echo   Copied eng.traineddata
)

REM Download if not exists
if not exist "%TESSDATA_DIR%\eng.traineddata" (
    echo   Downloading eng.traineddata...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/tesseract-ocr/tessdata_fast/raw/main/eng.traineddata' -OutFile '%TESSDATA_DIR%\eng.traineddata'"
    if exist "%TESSDATA_DIR%\eng.traineddata" (
        echo   Downloaded eng.traineddata
    ) else (
        echo   [WARNING] Failed to download tessdata
    )
)

echo.
echo ============================================
echo Done! Tesseract prepared in: %TESSERACT_DIR%
echo ============================================
echo.
echo Contents:
dir /b "%TESSERACT_DIR%"
echo.
echo Tessdata:
dir /b "%TESSDATA_DIR%"
echo.

pause
