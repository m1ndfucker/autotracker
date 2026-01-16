# bb_detector/platform_utils.py
import platform
import subprocess
from typing import Dict

def get_platform() -> str:
    system = platform.system()
    if system == 'Windows':
        return 'windows'
    elif system == 'Darwin':
        return 'macos'
    else:
        return 'linux'


def get_scale_factor() -> float:
    if get_platform() != 'macos':
        return 1.0

    try:
        from AppKit import NSScreen
        screen = NSScreen.mainScreen()
        return float(screen.backingScaleFactor())
    except ImportError:
        return 1.0
    except Exception:
        return 1.0


def check_macos_permissions() -> Dict[str, bool]:
    if get_platform() != 'macos':
        return {'screen': True, 'accessibility': True}

    result = {'screen': False, 'accessibility': False}

    # Check Screen Recording
    try:
        import mss
        sct = mss.mss()
        frame = sct.grab(sct.monitors[1])
        import numpy as np
        arr = np.array(frame)
        if arr.sum() > 0:
            result['screen'] = True
    except Exception:
        pass

    # Check Accessibility
    try:
        cmd = ['osascript', '-e', 'tell application "System Events" to return true']
        proc = subprocess.run(cmd, capture_output=True, timeout=2)
        result['accessibility'] = proc.returncode == 0
    except Exception:
        pass

    return result


def open_macos_permissions():
    if get_platform() != 'macos':
        return

    subprocess.run([
        'open',
        'x-apple.systempreferences:com.apple.preference.security?Privacy'
    ])
