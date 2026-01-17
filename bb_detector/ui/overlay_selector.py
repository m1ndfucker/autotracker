# bb_detector/ui/overlay_selector.py
"""Visual region selector with fullscreen transparent overlay."""
import sys
import subprocess
import json
import os
from pathlib import Path
from typing import Callable, Optional, Dict, Any

from ..platform_utils import get_platform


class OverlayRegionSelector:
    """
    Fullscreen transparent overlay for visual region selection.
    """

    def __init__(
        self,
        on_complete: Callable[[Dict[str, Any]], None],
        on_cancel: Callable[[], None],
    ):
        self.on_complete = on_complete
        self.on_cancel = on_cancel
        self._result_region: Optional[Dict] = None
        self._cancelled = False

    def show(self):
        """Show the fullscreen overlay and start selection."""
        platform = get_platform()

        if platform == 'macos':
            # macOS: pygame + screenshot (transparent overlay doesn't work)
            self._show_subprocess()
        elif platform == 'windows':
            # Windows: native win32gui with transparent overlay
            self._show_windows()
        else:
            print("[OverlaySelector] Platform not supported", flush=True)
            self.on_cancel()
            return

        if self._cancelled:
            self.on_cancel()
        elif self._result_region:
            self.on_complete(self._result_region)

    def _show_subprocess(self):
        """Cross-platform implementation using subprocess with pygame + screenshot."""
        import tempfile
        import time

        try:
            # Get path to overlay script
            script_path = Path(__file__).parent / "overlay_script.py"

            if not script_path.exists():
                print(f"[OverlaySelector] Script not found: {script_path}", flush=True)
                self._cancelled = True
                return

            # Create temp file for result
            fd, result_path = tempfile.mkstemp(suffix='.json', prefix='overlay_result_')
            os.close(fd)

            try:
                # Start subprocess completely detached
                proc = subprocess.Popen(
                    [sys.executable, str(script_path), result_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    text=True,  # Text mode for stderr
                    start_new_session=True
                )

                print("[OverlaySelector] Subprocess started, waiting for result...", flush=True)

                # Poll for result file with timeout
                start_time = time.time()
                timeout = 120  # 2 minutes

                while time.time() - start_time < timeout:
                    # Check if process finished
                    poll_result = proc.poll()
                    if poll_result is not None:
                        # Process finished
                        stderr = proc.stderr.read() if proc.stderr else ""
                        if stderr:
                            for line in stderr.strip().split('\n'):
                                print(f"[Overlay] {line}", flush=True)
                        break

                    # Check if result file has content
                    try:
                        if os.path.exists(result_path) and os.path.getsize(result_path) > 0:
                            break
                    except Exception:
                        pass

                    time.sleep(0.1)

                # Read result
                if os.path.exists(result_path) and os.path.getsize(result_path) > 0:
                    with open(result_path, 'r') as f:
                        content = f.read().strip()
                        if content:
                            data = json.loads(content)
                            if data.get("cancelled"):
                                self._cancelled = True
                            elif data.get("region"):
                                r = data["region"]
                                self._calculate_region(r["x1"], r["y1"], r["x2"], r["y2"])
                                print(f"[OverlaySelector] Region selected: {r}", flush=True)
                else:
                    print("[OverlaySelector] No result file or empty", flush=True)
                    self._cancelled = True

            finally:
                # Cleanup
                try:
                    os.unlink(result_path)
                except Exception:
                    pass
                # Kill subprocess if still running
                try:
                    proc.terminate()
                except Exception:
                    pass

        except Exception as e:
            print(f"[OverlaySelector] Error: {e}", flush=True)
            import traceback
            traceback.print_exc()
            self._cancelled = True

    def _show_windows(self):
        """Windows implementation using win32gui."""
        try:
            import win32gui
            import win32con
            import win32api
            import ctypes

            # Virtual screen = all monitors combined
            # SM_XVIRTUALSCREEN, SM_YVIRTUALSCREEN = top-left corner (can be negative!)
            # SM_CXVIRTUALSCREEN, SM_CYVIRTUALSCREEN = total width/height
            self._vscreen_x = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
            self._vscreen_y = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
            screen_width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
            screen_height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)

            print(f"[Overlay] Virtual screen: {self._vscreen_x},{self._vscreen_y} {screen_width}x{screen_height}", flush=True)

            wc = win32gui.WNDCLASS()
            wc.lpfnWndProc = self._windows_wnd_proc
            wc.hInstance = win32api.GetModuleHandle(None)
            wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_CROSS)
            wc.hbrBackground = win32gui.GetStockObject(win32con.BLACK_BRUSH)
            wc.lpszClassName = "OverlaySelectorWindow"

            try:
                win32gui.RegisterClass(wc)
            except Exception:
                pass

            # Position window at virtual screen origin (can be negative)
            self._hwnd = win32gui.CreateWindowEx(
                win32con.WS_EX_LAYERED | win32con.WS_EX_TOPMOST | win32con.WS_EX_TOOLWINDOW,
                "OverlaySelectorWindow",
                "",
                win32con.WS_POPUP,
                self._vscreen_x, self._vscreen_y, screen_width, screen_height,
                0, 0, wc.hInstance, None
            )

            win32gui.SetLayeredWindowAttributes(self._hwnd, 0, 90, win32con.LWA_ALPHA)

            # Initialize to None to detect first click properly
            self._win_start_x = None
            self._win_start_y = None
            self._win_current_x = None
            self._win_current_y = None
            self._win_dragging = False
            self._win_running = True

            win32gui.ShowWindow(self._hwnd, win32con.SW_SHOW)
            win32gui.UpdateWindow(self._hwnd)
            win32gui.SetForegroundWindow(self._hwnd)

            while self._win_running:
                msg = win32gui.GetMessage(self._hwnd, 0, 0)
                if msg[0] == 0:
                    break
                win32gui.TranslateMessage(msg[1])
                win32gui.DispatchMessage(msg[1])

        except Exception as e:
            print(f"[OverlaySelector] Windows error: {e}", flush=True)
            self._cancelled = True

    def _get_mouse_pos(self, lparam):
        """Extract signed x,y from lparam (handles multi-monitor negative coords)."""
        import ctypes
        # LOWORD/HIWORD return unsigned, but coords can be negative
        x = ctypes.c_short(lparam & 0xFFFF).value
        y = ctypes.c_short((lparam >> 16) & 0xFFFF).value
        # Convert to absolute screen coordinates
        return x + self._vscreen_x, y + self._vscreen_y

    def _windows_wnd_proc(self, hwnd, msg, wparam, lparam):
        """Windows message handler."""
        import win32gui
        import win32con
        import win32api

        if msg == win32con.WM_LBUTTONDOWN:
            x, y = self._get_mouse_pos(lparam)
            self._win_start_x = x
            self._win_start_y = y
            self._win_current_x = x
            self._win_current_y = y
            self._win_dragging = True
            win32gui.SetCapture(hwnd)
            print(f"[Overlay] Mouse down at {x},{y}", flush=True)
            return 0

        elif msg == win32con.WM_MOUSEMOVE:
            if self._win_dragging:
                x, y = self._get_mouse_pos(lparam)
                self._win_current_x = x
                self._win_current_y = y
                win32gui.InvalidateRect(hwnd, None, True)
            return 0

        elif msg == win32con.WM_LBUTTONUP:
            if self._win_dragging:
                self._win_dragging = False
                win32gui.ReleaseCapture()

                x1, y1 = self._win_start_x, self._win_start_y
                x2, y2 = self._win_current_x, self._win_current_y

                print(f"[Overlay] Mouse up: ({x1},{y1}) to ({x2},{y2})", flush=True)

                if x1 > x2:
                    x1, x2 = x2, x1
                if y1 > y2:
                    y1, y2 = y2, y1

                if (x2 - x1) >= 10 and (y2 - y1) >= 10:
                    self._calculate_region(x1, y1, x2, y2)
                    self._win_running = False
                    win32gui.DestroyWindow(hwnd)
                else:
                    # Too small, reset
                    self._win_start_x = None
                    self._win_start_y = None
            return 0

        elif msg == win32con.WM_KEYDOWN:
            if wparam == win32con.VK_ESCAPE:
                self._cancelled = True
                self._win_running = False
                win32gui.DestroyWindow(hwnd)
            return 0

        elif msg == win32con.WM_PAINT:
            hdc, ps = win32gui.BeginPaint(hwnd)
            # Only draw if we have valid start position and are dragging
            if self._win_dragging and self._win_start_x is not None:
                import win32ui
                dc = win32ui.CreateDCFromHandle(hdc)
                pen = win32ui.CreatePen(win32con.PS_SOLID, 2, win32api.RGB(255, 80, 80))
                old_pen = dc.SelectObject(pen)
                brush = win32gui.GetStockObject(win32con.HOLLOW_BRUSH)
                old_brush = dc.SelectObject(brush)
                # Convert absolute coords back to window coords for drawing
                x1 = self._win_start_x - self._vscreen_x
                y1 = self._win_start_y - self._vscreen_y
                x2 = self._win_current_x - self._vscreen_x
                y2 = self._win_current_y - self._vscreen_y
                dc.Rectangle(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
                dc.SelectObject(old_pen)
                dc.SelectObject(old_brush)
            win32gui.EndPaint(hwnd, ps)
            return 0

        elif msg == win32con.WM_DESTROY:
            self._win_running = False
            return 0

        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def _calculate_region(self, x1: int, y1: int, x2: int, y2: int):
        """Calculate window-relative region from absolute coordinates."""
        from ..window_utils import get_window_at_point

        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2

        window = get_window_at_point(center_x, center_y)

        if window:
            wb = window['bounds']
            x_percent = (x1 - wb['x']) / wb['width'] if wb['width'] > 0 else 0
            y_percent = (y1 - wb['y']) / wb['height'] if wb['height'] > 0 else 0
            w_percent = (x2 - x1) / wb['width'] if wb['width'] > 0 else 0
            h_percent = (y2 - y1) / wb['height'] if wb['height'] > 0 else 0

            x_percent = max(0.0, min(1.0, x_percent))
            y_percent = max(0.0, min(1.0, y_percent))
            w_percent = max(0.0, min(1.0 - x_percent, w_percent))
            h_percent = max(0.0, min(1.0 - y_percent, h_percent))

            self._result_region = {
                'window_name': window.get('name', ''),
                'window_title': window.get('title', ''),
                'x_percent': x_percent,
                'y_percent': y_percent,
                'w_percent': w_percent,
                'h_percent': h_percent,
                'absolute': {'x': x1, 'y': y1, 'width': x2 - x1, 'height': y2 - y1}
            }
        else:
            self._result_region = {
                'window_name': '',
                'window_title': '',
                'x_percent': 0,
                'y_percent': 0,
                'w_percent': 0,
                'h_percent': 0,
                'absolute': {'x': x1, 'y': y1, 'width': x2 - x1, 'height': y2 - y1}
            }


def show_overlay_selector(
    on_complete: Callable[[Dict[str, Any]], None],
    on_cancel: Callable[[], None],
    run_in_thread: bool = True
):
    """
    Show overlay selector.

    On macOS, runs in subprocess to avoid threading issues with AppKit.
    On Windows, can run in thread.
    """
    import threading

    def _run():
        selector = OverlayRegionSelector(on_complete, on_cancel)
        selector.show()

    if run_in_thread:
        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return thread
    else:
        _run()
        return None
