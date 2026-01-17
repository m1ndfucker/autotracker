# Visual Overlay Region Selector

## Summary

Replace the current F9 corner-click approach with a visual overlay where user draws a rectangle with mouse drag. The overlay captures raw screen coordinates, then existing window detection logic processes them.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Overlay (platform-specific)                            │
│  - Transparent fullscreen window                        │
│  - Draw rectangle during drag                           │
│  - Return {x1, y1, x2, y2} or {cancelled: true}         │
└─────────────────────┬───────────────────────────────────┘
                      │ raw screen coordinates
                      ▼
┌─────────────────────────────────────────────────────────┐
│  OverlayRegionSelector._coords_to_region()              │
│  - get_window_at_point(center_x, center_y)              │
│  - Calculate % coordinates relative to window           │
│  - Return region dict (same format as F9 selector)      │
└─────────────────────────────────────────────────────────┘
```

## Files

| File | Action | Description |
|------|--------|-------------|
| `bb_detector/ui/overlay_script.py` | Rewrite | macOS subprocess - minimal, returns coords only |
| `bb_detector/ui/overlay_selector.py` | Rewrite | Main class with platform dispatch + coords→region |
| `bb_detector/ui/tabs/calibration.py` | Minor edit | Wire up the selector |
| `bb_detector/ui/corner_selector.py` | Keep | F9 fallback remains available |

## macOS Implementation

Subprocess (`overlay_script.py`) because AppKit requires main thread.

**Input:** result_file path via argv
**Output:** JSON file with `{cancelled, x1, y1, x2, y2}`

```python
# Minimal subprocess responsibilities:
# 1. Show transparent fullscreen NSWindow
# 2. Draw rectangle on drag (blue fill + border + size label)
# 3. On mouseUp: write coords to file, exit
# 4. On ESC: write cancelled, exit
```

**Visual style (Bandicam-like):**
- Background: nearly invisible (alpha 0.01) to capture clicks
- Rectangle fill: `rgba(0.3, 0.5, 1.0, 0.2)`
- Rectangle border: `rgba(0.2, 0.5, 1.0, 1.0)`, 2px
- Size label: white text on black background

**Coordinate conversion:**
NSView Y is flipped (0 at bottom). Convert: `screen_y = screen_height - view_y`

## Windows Implementation

In-process using win32gui (no subprocess needed).

```python
# Same responsibilities as macOS:
# 1. CreateWindowEx with WS_EX_LAYERED | WS_EX_TOPMOST
# 2. WM_PAINT draws rectangle during drag
# 3. WM_LBUTTONUP returns coords
# 4. WM_KEYDOWN(VK_ESCAPE) cancels
```

## Main Class API

```python
class OverlayRegionSelector:
    def __init__(self, on_complete: Callable[[dict], None], on_cancel: Callable[[], None]):
        pass

    def show(self):
        """Show overlay, block until complete or cancelled."""
        pass
```

**Region dict format (same as F9 selector):**
```python
{
    'window_name': str,
    'window_title': str,
    'x_percent': float,  # 0.0-1.0
    'y_percent': float,
    'w_percent': float,
    'h_percent': float,
    'absolute': {'x': int, 'y': int, 'width': int, 'height': int}
}
```

## Calibration Tab Integration

```python
def _on_select_region_clicked(self):
    selector = OverlayRegionSelector(
        on_complete=self._on_region_selected,
        on_cancel=self._on_region_cancelled
    )
    threading.Thread(target=selector.show, daemon=True).start()
```

## Controls

| Action | Result |
|--------|--------|
| Mouse drag | Draw selection rectangle |
| Mouse release | Confirm selection (if >= 10x10 px) |
| ESC | Cancel selection |

## Validation

1. Run app: `python -m bb_detector.main`
2. Go to Calibration tab
3. Click "Select Region"
4. Overlay appears (nearly transparent)
5. Draw rectangle over target area
6. Release mouse → overlay closes
7. UI shows detected window + region percentages
8. Test with "Capture & Test" button
