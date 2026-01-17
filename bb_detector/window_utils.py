# bb_detector/window_utils.py
"""Cross-platform window utilities for macOS and Windows."""
from typing import Optional, Dict, Any, List
import numpy as np
from .platform_utils import get_platform


def get_window_at_point(x: int, y: int) -> Optional[Dict[str, Any]]:
    """Find the window under the given screen coordinates.

    Args:
        x: Screen X coordinate (pixels from left)
        y: Screen Y coordinate (pixels from top)

    Returns:
        Dictionary with window info or None if no window found.
        Keys: 'name' (app name), 'title' (window title), 'bounds' (x, y, width, height)
    """
    platform = get_platform()

    if platform == 'macos':
        return _get_window_at_point_macos(x, y)
    elif platform == 'windows':
        return _get_window_at_point_windows(x, y)

    return None


def _get_window_at_point_macos(x: int, y: int) -> Optional[Dict[str, Any]]:
    """macOS implementation using Quartz."""
    try:
        from Quartz import (
            CGWindowListCopyWindowInfo,
            kCGWindowListOptionOnScreenOnly,
            kCGNullWindowID
        )

        windows = CGWindowListCopyWindowInfo(
            kCGWindowListOptionOnScreenOnly,
            kCGNullWindowID
        )

        if not windows:
            return None

        # Iterate windows (front-to-back order)
        for window in windows:
            bounds = window.get('kCGWindowBounds', {})
            wx = bounds.get('X', 0)
            wy = bounds.get('Y', 0)
            ww = bounds.get('Width', 0)
            wh = bounds.get('Height', 0)

            # Check if point is inside window bounds
            if wx <= x <= wx + ww and wy <= y <= wy + wh:
                owner_name = window.get('kCGWindowOwnerName', '')
                window_name = window.get('kCGWindowName', '')
                window_id = window.get('kCGWindowNumber', 0)

                # Skip system UI elements (menubar, dock, etc)
                if owner_name in ('Window Server', 'Dock', 'SystemUIServer'):
                    continue

                return {
                    'name': owner_name,
                    'title': window_name,
                    'window_id': int(window_id),
                    'bounds': {
                        'x': int(wx),
                        'y': int(wy),
                        'width': int(ww),
                        'height': int(wh)
                    }
                }

        return None

    except (ImportError, Exception):
        return None


def _get_window_at_point_windows(x: int, y: int) -> Optional[Dict[str, Any]]:
    """Windows implementation using win32gui."""
    try:
        import win32gui
        import win32process
        import psutil

        # Get window handle at point
        hwnd = win32gui.WindowFromPoint((x, y))
        if not hwnd:
            return None

        # Get root window (in case we hit a child)
        root_hwnd = win32gui.GetAncestor(hwnd, 2)  # GA_ROOT = 2
        if root_hwnd:
            hwnd = root_hwnd

        # Get window rect
        try:
            rect = win32gui.GetWindowRect(hwnd)
            wx, wy, wx2, wy2 = rect
            ww = wx2 - wx
            wh = wy2 - wy
        except Exception:
            return None

        # Get window title
        window_title = win32gui.GetWindowText(hwnd)

        # Get process name
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            process_name = process.name()
        except Exception:
            process_name = ''

        return {
            'name': process_name,
            'title': window_title,
            'bounds': {
                'x': int(wx),
                'y': int(wy),
                'width': int(ww),
                'height': int(wh)
            },
            'hwnd': hwnd
        }

    except (ImportError, Exception):
        return None


def find_window_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Find a window by application name (case-insensitive partial match).

    Args:
        name: Application name to search for (e.g., 'VLC', 'OBS')

    Returns:
        Dictionary with window info or None if not found.
        Keys: 'name' (app name), 'title' (window title), 'bounds' (x, y, width, height)
    """
    platform = get_platform()

    if platform == 'macos':
        return _find_window_by_name_macos(name)
    elif platform == 'windows':
        return _find_window_by_name_windows(name)

    return None


def _find_window_by_name_macos(name: str) -> Optional[Dict[str, Any]]:
    """macOS implementation using Quartz."""
    try:
        from Quartz import (
            CGWindowListCopyWindowInfo,
            kCGWindowListOptionOnScreenOnly,
            kCGNullWindowID
        )

        windows = CGWindowListCopyWindowInfo(
            kCGWindowListOptionOnScreenOnly,
            kCGNullWindowID
        )

        if not windows:
            return None

        name_lower = name.lower()

        for window in windows:
            owner_name = window.get('kCGWindowOwnerName', '')

            if name_lower in owner_name.lower():
                bounds = window.get('kCGWindowBounds', {})
                window_name = window.get('kCGWindowName', '')
                window_id = window.get('kCGWindowNumber', 0)

                return {
                    'name': owner_name,
                    'title': window_name,
                    'window_id': int(window_id),
                    'bounds': {
                        'x': int(bounds.get('X', 0)),
                        'y': int(bounds.get('Y', 0)),
                        'width': int(bounds.get('Width', 0)),
                        'height': int(bounds.get('Height', 0))
                    }
                }

        return None

    except (ImportError, Exception):
        return None


def _find_window_by_name_windows(name: str) -> Optional[Dict[str, Any]]:
    """Windows implementation using win32gui."""
    try:
        import win32gui
        import win32process
        import psutil

        name_lower = name.lower()
        result = None

        def enum_callback(hwnd, _):
            nonlocal result
            if result is not None:
                return True

            if not win32gui.IsWindowVisible(hwnd):
                return True

            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                process = psutil.Process(pid)
                process_name = process.name()

                if name_lower in process_name.lower():
                    rect = win32gui.GetWindowRect(hwnd)
                    wx, wy, wx2, wy2 = rect
                    ww = wx2 - wx
                    wh = wy2 - wy

                    # Skip zero-size windows
                    if ww <= 0 or wh <= 0:
                        return True

                    result = {
                        'name': process_name,
                        'title': win32gui.GetWindowText(hwnd),
                        'bounds': {
                            'x': int(wx),
                            'y': int(wy),
                            'width': int(ww),
                            'height': int(wh)
                        },
                        'hwnd': hwnd
                    }
                    return True
            except Exception:
                pass

            return True

        win32gui.EnumWindows(enum_callback, None)
        return result

    except (ImportError, Exception):
        return None


def get_cursor_position() -> tuple[int, int]:
    """Get current cursor position on screen.

    Returns:
        Tuple of (x, y) screen coordinates.
    """
    platform = get_platform()

    if platform == 'macos':
        return _get_cursor_position_macos()
    elif platform == 'windows':
        return _get_cursor_position_windows()

    # Fallback using pynput (cross-platform)
    return _get_cursor_position_pynput()


def _get_cursor_position_macos() -> tuple[int, int]:
    """macOS implementation using Quartz."""
    try:
        from Quartz import CGEventCreate, CGEventGetLocation

        event = CGEventCreate(None)
        if event:
            location = CGEventGetLocation(event)
            return (int(location.x), int(location.y))

        return _get_cursor_position_pynput()

    except (ImportError, Exception):
        return _get_cursor_position_pynput()


def _get_cursor_position_windows() -> tuple[int, int]:
    """Windows implementation using win32gui."""
    try:
        import win32gui
        point = win32gui.GetCursorPos()
        return (int(point[0]), int(point[1]))

    except (ImportError, Exception):
        return _get_cursor_position_pynput()


def _get_cursor_position_pynput() -> tuple[int, int]:
    """Fallback using pynput (cross-platform)."""
    try:
        from pynput.mouse import Controller
        mouse = Controller()
        pos = mouse.position
        return (int(pos[0]), int(pos[1]))
    except Exception:
        return (0, 0)


def list_visible_windows() -> List[Dict[str, Any]]:
    """List all visible windows on screen.

    Returns:
        List of window dictionaries with 'name', 'title', 'bounds' keys.
    """
    platform = get_platform()

    if platform == 'macos':
        return _list_visible_windows_macos()
    elif platform == 'windows':
        return _list_visible_windows_windows()

    return []


def _list_visible_windows_macos() -> List[Dict[str, Any]]:
    """macOS implementation."""
    try:
        from Quartz import (
            CGWindowListCopyWindowInfo,
            kCGWindowListOptionOnScreenOnly,
            kCGNullWindowID
        )

        windows = CGWindowListCopyWindowInfo(
            kCGWindowListOptionOnScreenOnly,
            kCGNullWindowID
        )

        if not windows:
            return []

        result = []
        for window in windows:
            owner_name = window.get('kCGWindowOwnerName', '')

            # Skip system UI elements
            if owner_name in ('Window Server', 'Dock', 'SystemUIServer', ''):
                continue

            bounds = window.get('kCGWindowBounds', {})

            # Skip zero-size windows
            if bounds.get('Width', 0) <= 0 or bounds.get('Height', 0) <= 0:
                continue

            result.append({
                'name': owner_name,
                'title': window.get('kCGWindowName', ''),
                'bounds': {
                    'x': int(bounds.get('X', 0)),
                    'y': int(bounds.get('Y', 0)),
                    'width': int(bounds.get('Width', 0)),
                    'height': int(bounds.get('Height', 0))
                }
            })

        return result

    except (ImportError, Exception):
        return []


def _list_visible_windows_windows() -> List[Dict[str, Any]]:
    """Windows implementation."""
    try:
        import win32gui
        import win32process
        import psutil

        result = []

        def enum_callback(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return True

            try:
                rect = win32gui.GetWindowRect(hwnd)
                wx, wy, wx2, wy2 = rect
                ww = wx2 - wx
                wh = wy2 - wy

                # Skip zero-size windows
                if ww <= 0 or wh <= 0:
                    return True

                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                process = psutil.Process(pid)
                process_name = process.name()

                result.append({
                    'name': process_name,
                    'title': win32gui.GetWindowText(hwnd),
                    'bounds': {
                        'x': int(wx),
                        'y': int(wy),
                        'width': int(ww),
                        'height': int(wh)
                    },
                    'hwnd': hwnd
                })
            except Exception:
                pass

            return True

        win32gui.EnumWindows(enum_callback, None)
        return result

    except (ImportError, Exception):
        return []


def capture_window_region(
    window_name: str,
    x_percent: float,
    y_percent: float,
    w_percent: float,
    h_percent: float
) -> Optional[np.ndarray]:
    """Capture a region inside a specific window (ignores windows on top).

    Args:
        window_name: Application name to find the window
        x_percent: X offset as percentage of window width (0.0-1.0)
        y_percent: Y offset as percentage of window height (0.0-1.0)
        w_percent: Region width as percentage of window width (0.0-1.0)
        h_percent: Region height as percentage of window height (0.0-1.0)

    Returns:
        numpy array with RGB image data, or None if capture failed.
    """
    platform = get_platform()

    if platform == 'macos':
        return _capture_window_region_macos(window_name, x_percent, y_percent, w_percent, h_percent)
    elif platform == 'windows':
        return _capture_window_region_windows(window_name, x_percent, y_percent, w_percent, h_percent)

    return None


def _capture_window_region_macos(
    window_name: str,
    x_percent: float,
    y_percent: float,
    w_percent: float,
    h_percent: float
) -> Optional[np.ndarray]:
    """macOS: Capture window region using CGWindowListCreateImage."""
    try:
        from Quartz import (
            CGWindowListCreateImage,
            CGWindowListCopyWindowInfo,
            kCGWindowListOptionIncludingWindow,
            kCGWindowListOptionOnScreenOnly,
            kCGWindowImageBoundsIgnoreFraming,
            kCGNullWindowID,
            CGRectNull
        )
        from Quartz.CoreGraphics import CGImageGetWidth, CGImageGetHeight, CGImageGetDataProvider, CGDataProviderCopyData

        # Find window by name
        windows = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
        if not windows:
            return None

        target_window = None
        name_lower = window_name.lower()

        for window in windows:
            owner_name = window.get('kCGWindowOwnerName', '')
            if name_lower in owner_name.lower():
                target_window = window
                break

        if not target_window:
            return None

        window_id = target_window.get('kCGWindowNumber', 0)
        if not window_id:
            return None

        # Capture only this window (ignores windows on top)
        image = CGWindowListCreateImage(
            CGRectNull,  # Capture full window bounds
            kCGWindowListOptionIncludingWindow,
            window_id,
            kCGWindowImageBoundsIgnoreFraming  # Ignore window frame/shadow
        )

        if not image:
            return None

        # Get image dimensions
        width = CGImageGetWidth(image)
        height = CGImageGetHeight(image)

        if width <= 0 or height <= 0:
            return None

        # Convert CGImage to numpy array
        data_provider = CGImageGetDataProvider(image)
        data = CGDataProviderCopyData(data_provider)

        # CGImage data is BGRA
        arr = np.frombuffer(data, dtype=np.uint8)
        arr = arr.reshape((height, width, 4))

        # Convert BGRA to RGB
        rgb = arr[:, :, [2, 1, 0]].copy()

        # Calculate region in pixels
        region_x = int(x_percent * width)
        region_y = int(y_percent * height)
        region_w = int(w_percent * width)
        region_h = int(h_percent * height)

        # Clamp to valid bounds
        region_x = max(0, min(region_x, width - 1))
        region_y = max(0, min(region_y, height - 1))
        region_w = max(1, min(region_w, width - region_x))
        region_h = max(1, min(region_h, height - region_y))

        # Extract region
        region = rgb[region_y:region_y + region_h, region_x:region_x + region_w]

        return region

    except Exception as e:
        print(f"[WindowCapture] macOS error: {e}", flush=True)
        return None


def _capture_window_region_windows(
    window_name: str,
    x_percent: float,
    y_percent: float,
    w_percent: float,
    h_percent: float
) -> Optional[np.ndarray]:
    """Windows: Capture window region using PrintWindow."""
    try:
        import win32gui
        import win32ui
        import win32con
        import win32process
        import psutil

        # Find window by process name
        name_lower = window_name.lower()
        target_hwnd = None

        def enum_callback(hwnd, _):
            nonlocal target_hwnd
            if target_hwnd is not None:
                return True

            if not win32gui.IsWindowVisible(hwnd):
                return True

            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                process = psutil.Process(pid)
                process_name = process.name()

                if name_lower in process_name.lower():
                    target_hwnd = hwnd
            except Exception:
                pass

            return True

        win32gui.EnumWindows(enum_callback, None)

        if not target_hwnd:
            return None

        # Get window dimensions
        rect = win32gui.GetClientRect(target_hwnd)
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]

        if width <= 0 or height <= 0:
            return None

        # Create device contexts
        hwnd_dc = win32gui.GetWindowDC(target_hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()

        # Create bitmap
        bitmap = win32ui.CreateBitmap()
        bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
        save_dc.SelectObject(bitmap)

        # Capture window content (works even if window is behind others)
        result = win32gui.PrintWindow(target_hwnd, save_dc.GetSafeHdc(), win32con.PW_CLIENTONLY)

        if not result:
            # Fallback to BitBlt
            save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), win32con.SRCCOPY)

        # Convert to numpy array
        bmp_info = bitmap.GetInfo()
        bmp_str = bitmap.GetBitmapBits(True)
        img = np.frombuffer(bmp_str, dtype=np.uint8)
        img = img.reshape((bmp_info['bmHeight'], bmp_info['bmWidth'], 4))

        # Cleanup
        win32gui.DeleteObject(bitmap.GetHandle())
        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(target_hwnd, hwnd_dc)

        # Convert BGRA to RGB
        rgb = img[:, :, [2, 1, 0]].copy()

        # Calculate region in pixels
        region_x = int(x_percent * width)
        region_y = int(y_percent * height)
        region_w = int(w_percent * width)
        region_h = int(h_percent * height)

        # Clamp to valid bounds
        region_x = max(0, min(region_x, width - 1))
        region_y = max(0, min(region_y, height - 1))
        region_w = max(1, min(region_w, width - region_x))
        region_h = max(1, min(region_h, height - region_y))

        # Extract region
        region = rgb[region_y:region_y + region_h, region_x:region_x + region_w]

        return region

    except Exception as e:
        print(f"[WindowCapture] Windows error: {e}", flush=True)
        return None
