# bb_detector/tesseract_utils.py
"""
Tesseract OCR utilities - auto-detect, download, and configure Tesseract.

Features:
- Auto-detect bundled Tesseract (PyInstaller builds)
- Auto-detect system Tesseract
- Auto-download portable Tesseract if not found (Windows only)
"""

import os
import sys
import shutil
import zipfile
import tempfile
from pathlib import Path
from typing import Optional
import urllib.request
import ssl

from .platform_utils import get_platform

# Tesseract portable download URLs (UB Mannheim)
TESSERACT_PORTABLE_URL = "https://github.com/UB-Mannheim/tesseract/releases/download/v5.5.0.20241111/tesseract-ocr-w64-setup-5.5.0.20241111.exe"

# Fast tessdata (smaller, faster)
TESSDATA_ENG_URL = "https://github.com/tesseract-ocr/tessdata_fast/raw/main/eng.traineddata"

# Alternative mirrors (in case GitHub is blocked)
TESSDATA_MIRRORS = [
    "https://github.com/tesseract-ocr/tessdata_fast/raw/main/eng.traineddata",
    "https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/main/eng.traineddata",
]


def get_app_data_dir() -> Path:
    """Get application data directory for storing Tesseract."""
    if get_platform() == 'windows':
        base = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local'))
    else:
        base = Path.home() / '.local' / 'share'

    app_dir = base / 'BBDeathDetector'
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_tesseract_dir() -> Path:
    """Get directory where Tesseract should be stored."""
    return get_app_data_dir() / 'tesseract'


def get_bundled_tesseract_path() -> Optional[Path]:
    """
    Get path to bundled Tesseract (for PyInstaller builds).
    """
    # PyInstaller bundle
    if hasattr(sys, '_MEIPASS'):
        bundled = Path(sys._MEIPASS) / 'assets' / 'tesseract'
        if (bundled / 'tesseract.exe').exists():
            return bundled

    # Next to executable
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).parent
        bundled = exe_dir / 'assets' / 'tesseract'
        if (bundled / 'tesseract.exe').exists():
            return bundled

    # Development: relative to source
    source_dir = Path(__file__).parent.parent
    bundled = source_dir / 'assets' / 'tesseract'
    if (bundled / 'tesseract.exe').exists():
        return bundled

    # Auto-downloaded location
    downloaded = get_tesseract_dir()
    if (downloaded / 'tesseract.exe').exists():
        return downloaded

    return None


def get_tesseract_cmd() -> str:
    """
    Get path to tesseract executable.
    """
    # Check bundled/downloaded first
    bundled_dir = get_bundled_tesseract_path()
    if bundled_dir:
        tesseract_exe = bundled_dir / 'tesseract.exe'
        if tesseract_exe.exists():
            return str(tesseract_exe)

    # Check PATH
    tesseract_in_path = shutil.which('tesseract')
    if tesseract_in_path:
        return tesseract_in_path

    # Common Windows locations
    if get_platform() == 'windows':
        common_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        ]
        for path in common_paths:
            if os.path.exists(path):
                return path

    return 'tesseract'


def get_tessdata_dir() -> Optional[str]:
    """Get path to tessdata directory."""
    bundled_dir = get_bundled_tesseract_path()
    if bundled_dir:
        tessdata = bundled_dir / 'tessdata'
        if tessdata.exists() and any(tessdata.glob('*.traineddata')):
            return str(tessdata)

    env_tessdata = os.environ.get('TESSDATA_PREFIX')
    if env_tessdata and os.path.exists(env_tessdata):
        return env_tessdata

    return None


def download_file(url: str, dest: Path, desc: str = "", progress_callback=None) -> bool:
    """Download file with progress."""
    try:
        print(f"[Tesseract] Downloading {desc or url}...")

        # Create SSL context that works with most systems
        ctx = ssl.create_default_context()

        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

        with urllib.request.urlopen(req, context=ctx, timeout=60) as response:
            total = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            chunk_size = 8192

            with open(dest, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)

                    if progress_callback and total > 0:
                        progress_callback(downloaded, total)
                    elif total > 0:
                        pct = int(downloaded * 100 / total)
                        print(f"\r[Tesseract]   {pct}%", end='', flush=True)

        print()
        return True

    except Exception as e:
        print(f"\n[Tesseract] Download failed: {e}")
        return False


def download_tessdata(tesseract_dir: Path) -> bool:
    """Download tessdata (eng.traineddata)."""
    tessdata_dir = tesseract_dir / 'tessdata'
    tessdata_dir.mkdir(parents=True, exist_ok=True)

    eng_file = tessdata_dir / 'eng.traineddata'
    if eng_file.exists():
        print(f"[Tesseract] Tessdata already exists: {eng_file}")
        return True

    # Try mirrors
    for url in TESSDATA_MIRRORS:
        if download_file(url, eng_file, "eng.traineddata"):
            return True

    return False


def download_tesseract_portable() -> Optional[Path]:
    """
    Download portable Tesseract for Windows.

    Downloads minimal files needed for OCR:
    - tesseract.exe
    - Required DLLs
    - eng.traineddata
    """
    if get_platform() != 'windows':
        print("[Tesseract] Auto-download only supported on Windows")
        return None

    tesseract_dir = get_tesseract_dir()
    tesseract_exe = tesseract_dir / 'tesseract.exe'

    if tesseract_exe.exists():
        print(f"[Tesseract] Already downloaded: {tesseract_dir}")
        return tesseract_dir

    print("[Tesseract] Tesseract not found, downloading...")
    print(f"[Tesseract] Install location: {tesseract_dir}")

    tesseract_dir.mkdir(parents=True, exist_ok=True)

    # Download tessdata first (smaller, more likely to succeed)
    if not download_tessdata(tesseract_dir):
        print("[Tesseract] Failed to download tessdata")
        return None

    # For full portable Tesseract, we need the exe and DLLs
    # The UB Mannheim installer is an NSIS exe, not a zip
    # We'll need to either:
    # 1. Ask user to install it manually
    # 2. Use a different source
    # 3. Extract from the installer using 7z

    # For now, let's check if user has Tesseract installed and copy from there
    system_tesseract = shutil.which('tesseract')
    if not system_tesseract:
        # Check common paths
        for path in [
            r"C:\Program Files\Tesseract-OCR",
            r"C:\Program Files (x86)\Tesseract-OCR",
        ]:
            if os.path.exists(os.path.join(path, 'tesseract.exe')):
                system_tesseract = os.path.join(path, 'tesseract.exe')
                break

    if system_tesseract:
        # Copy from system installation
        src_dir = Path(system_tesseract).parent
        print(f"[Tesseract] Copying from system: {src_dir}")

        try:
            # Copy exe
            shutil.copy2(src_dir / 'tesseract.exe', tesseract_dir / 'tesseract.exe')

            # Copy DLLs
            for dll in src_dir.glob('*.dll'):
                shutil.copy2(dll, tesseract_dir / dll.name)

            print(f"[Tesseract] Copied to: {tesseract_dir}")
            return tesseract_dir

        except Exception as e:
            print(f"[Tesseract] Failed to copy: {e}")

    # If no system Tesseract, show instructions
    print()
    print("=" * 50)
    print("[Tesseract] MANUAL INSTALLATION REQUIRED")
    print("=" * 50)
    print()
    print("Please install Tesseract OCR:")
    print("  https://github.com/UB-Mannheim/tesseract/wiki")
    print()
    print("After installation, restart the app.")
    print("=" * 50)

    return None


def configure_pytesseract() -> bool:
    """
    Configure pytesseract to use bundled, downloaded, or system Tesseract.

    Auto-downloads Tesseract on Windows if not found.
    """
    try:
        import pytesseract

        # Check if Tesseract is available
        bundled_dir = get_bundled_tesseract_path()

        # If not found and on Windows, try to download
        if not bundled_dir and get_platform() == 'windows':
            bundled_dir = download_tesseract_portable()

        # Set tesseract command
        if bundled_dir:
            tesseract_cmd = str(bundled_dir / 'tesseract.exe')
            tessdata_dir = str(bundled_dir / 'tessdata')
        else:
            tesseract_cmd = get_tesseract_cmd()
            tessdata_dir = get_tessdata_dir()

        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

        if tessdata_dir:
            os.environ['TESSDATA_PREFIX'] = tessdata_dir

        print(f"[Tesseract] Using: {tesseract_cmd}")
        if tessdata_dir:
            print(f"[Tesseract] Tessdata: {tessdata_dir}")

        return True

    except ImportError:
        print("[Tesseract] pytesseract not installed")
        return False
    except Exception as e:
        print(f"[Tesseract] Error: {e}")
        return False


def check_tesseract() -> bool:
    """Check if Tesseract is available and working."""
    try:
        import pytesseract
        configure_pytesseract()
        version = pytesseract.get_tesseract_version()
        print(f"[Tesseract] Version: {version}")
        return True
    except Exception as e:
        print(f"[Tesseract] Not available: {e}")
        return False
