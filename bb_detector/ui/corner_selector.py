# bb_detector/ui/corner_selector.py
"""Corner-click region selector using F9 hotkey."""
import threading
from typing import Callable, Optional, Dict, Any

from ..window_utils import get_window_at_point, get_cursor_position


class CornerSelector:
    """
    Window-relative region selector using F9 hotkey.

    Note: This class now uses polling instead of a separate keyboard listener
    to avoid conflicts with the main GlobalHotkeys.

    Usage:
    1. Call start() to begin selection mode
    2. Call on_f9_pressed() when F9 is pressed (from external hotkey system)
    3. First F9 captures the window under cursor + coordinates
    4. Second F9 completes selection, calculates relative coordinates
    """

    def __init__(
        self,
        on_complete: Callable[[Dict[str, Any]], None],
        on_cancel: Callable[[], None],
        on_progress: Optional[Callable[[str, int], None]] = None
    ):
        """
        Args:
            on_complete: Called with region dict when selection completes.
            on_cancel: Called when selection is cancelled.
            on_progress: Optional callback for UI updates (message, step 0-2).
        """
        self.on_complete = on_complete
        self.on_cancel = on_cancel
        self.on_progress = on_progress

        self._corners: list[tuple[int, int]] = []
        self._target_window: Optional[Dict[str, Any]] = None
        self._active = False
        self._lock = threading.Lock()

    @property
    def is_active(self) -> bool:
        """Check if selection is in progress."""
        return self._active

    def start(self):
        """Start the region selection process."""
        with self._lock:
            if self._active:
                return

            self._active = True
            self._corners = []
            self._target_window = None

        # Notify UI
        if self.on_progress:
            self.on_progress("Move cursor to TOP-LEFT corner and press F9", 0)

    def stop(self):
        """Stop the region selection process."""
        with self._lock:
            self._active = False

    def on_f9_pressed(self):
        """
        Handle F9 key press. Call this from external hotkey system.

        Returns:
            True if the event was handled, False if selector is not active.
        """
        if not self._active:
            return False

        self._on_hotkey()
        return True

    def cancel(self):
        """Cancel the selection process."""
        self.stop()

        if self.on_progress:
            self.on_progress("Selection cancelled", -1)

        self.on_cancel()

    def _on_hotkey(self):
        """Handle F9 hotkey press."""
        with self._lock:
            if not self._active:
                return

            # Get cursor position
            pos = get_cursor_position()

            if len(self._corners) == 0:
                # First corner - determine target window
                self._target_window = get_window_at_point(pos[0], pos[1])

                if not self._target_window:
                    if self.on_progress:
                        self.on_progress("No window found. Try again.", 0)
                    return

                self._corners.append(pos)

                # Notify UI for second corner
                if self.on_progress:
                    window_name = self._target_window.get('name', 'Unknown')
                    self.on_progress(
                        f"Window: {window_name}\n"
                        f"Move cursor to BOTTOM-RIGHT corner and press F9",
                        1
                    )

            elif len(self._corners) == 1:
                # Second corner - complete selection
                self._corners.append(pos)
                self._complete()

    def _complete(self):
        """Complete selection and calculate relative coordinates."""
        if not self._target_window or len(self._corners) != 2:
            self.cancel()
            return

        self._active = False

        # Get window bounds
        wb = self._target_window['bounds']

        # Get corner coordinates
        x1, y1 = self._corners[0]
        x2, y2 = self._corners[1]

        # Normalize (ensure x1,y1 is top-left)
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1

        # Calculate relative coordinates (percentage of window size)
        x_percent = (x1 - wb['x']) / wb['width'] if wb['width'] > 0 else 0
        y_percent = (y1 - wb['y']) / wb['height'] if wb['height'] > 0 else 0
        w_percent = (x2 - x1) / wb['width'] if wb['width'] > 0 else 0
        h_percent = (y2 - y1) / wb['height'] if wb['height'] > 0 else 0

        # Clamp to valid range
        x_percent = max(0.0, min(1.0, x_percent))
        y_percent = max(0.0, min(1.0, y_percent))
        w_percent = max(0.0, min(1.0 - x_percent, w_percent))
        h_percent = max(0.0, min(1.0 - y_percent, h_percent))

        region = {
            'window_name': self._target_window.get('name', ''),
            'window_title': self._target_window.get('title', ''),
            'x_percent': x_percent,
            'y_percent': y_percent,
            'w_percent': w_percent,
            'h_percent': h_percent,
            # Also store absolute coordinates as fallback
            'absolute': {
                'x': x1,
                'y': y1,
                'width': x2 - x1,
                'height': y2 - y1
            }
        }

        # Notify UI
        if self.on_progress:
            self.on_progress(
                f"Region selected: {w_percent*100:.1f}% x {h_percent*100:.1f}%",
                2
            )

        # Call completion callback
        self.on_complete(region)


def calculate_absolute_region(
    region: Dict[str, Any],
    window_bounds: Optional[Dict[str, int]] = None
) -> Optional[Dict[str, int]]:
    """
    Calculate absolute screen coordinates from a window-relative region.

    Args:
        region: Region dict with x_percent, y_percent, w_percent, h_percent, window_name
        window_bounds: Optional pre-fetched window bounds. If None, will look up by name.

    Returns:
        Dict with 'x', 'y', 'width', 'height' in absolute screen coordinates,
        or None if window not found.
    """
    from ..window_utils import find_window_by_name

    # If window bounds not provided, look up by name
    if window_bounds is None:
        window_name = region.get('window_name', '')
        if not window_name:
            # Fallback to absolute coordinates
            return region.get('absolute')

        window = find_window_by_name(window_name)
        if not window:
            # Window not found, fallback to absolute
            return region.get('absolute')

        window_bounds = window['bounds']

    # Calculate absolute coordinates from percentages
    x = int(window_bounds['x'] + region['x_percent'] * window_bounds['width'])
    y = int(window_bounds['y'] + region['y_percent'] * window_bounds['height'])
    w = int(region['w_percent'] * window_bounds['width'])
    h = int(region['h_percent'] * window_bounds['height'])

    return {
        'x': x,
        'y': y,
        'width': w,
        'height': h
    }
