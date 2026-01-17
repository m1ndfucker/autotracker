#!/usr/bin/env python3
"""
Download portable Tesseract OCR for bundling with the app.

This script downloads Tesseract binaries and tessdata for Windows.
The files will be placed in assets/tesseract/ for bundling.
"""

import os
import sys
import zipfile
import shutil
from pathlib import Path
import urllib.request

# Tesseract portable URLs
TESSERACT_URL = "https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.5.0.20241111.exe"
# Alternative: use UB-Mannheim portable zip
TESSERACT_ZIP_URL = "https://github.com/UB-Mannheim/tesseract/releases/download/v5.5.0.20241111/tesseract-ocr-w64-setup-5.5.0.20241111.exe"

# Minimal tessdata (eng only, ~4MB)
TESSDATA_URL = "https://github.com/tesseract-ocr/tessdata_fast/raw/main/eng.traineddata"

def download_file(url: str, dest: Path, desc: str = ""):
    """Download file with progress."""
    print(f"Downloading {desc or url}...")

    def progress(count, block_size, total_size):
        percent = int(count * block_size * 100 / total_size) if total_size > 0 else 0
        sys.stdout.write(f"\r  {percent}%")
        sys.stdout.flush()

    urllib.request.urlretrieve(url, dest, progress)
    print()

def main():
    root = Path(__file__).parent.parent
    tesseract_dir = root / "assets" / "tesseract"
    tessdata_dir = tesseract_dir / "tessdata"

    # Create directories
    tesseract_dir.mkdir(parents=True, exist_ok=True)
    tessdata_dir.mkdir(parents=True, exist_ok=True)

    # Download tessdata (eng)
    eng_file = tessdata_dir / "eng.traineddata"
    if not eng_file.exists():
        download_file(TESSDATA_URL, eng_file, "English tessdata")
        print(f"  Saved to: {eng_file}")
    else:
        print(f"  Already exists: {eng_file}")

    print()
    print("=" * 50)
    print("Tessdata downloaded!")
    print()
    print("For full Tesseract binaries, download manually from:")
    print("  https://github.com/UB-Mannheim/tesseract/wiki")
    print()
    print("Then copy these files to assets/tesseract/:")
    print("  - tesseract.exe")
    print("  - *.dll files")
    print("=" * 50)

if __name__ == "__main__":
    main()
