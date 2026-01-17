# bb_detector/ui/tabs/calibration.py
"""Calibration tab - screen region selection and OCR detection testing."""
import dearpygui.dearpygui as dpg
from typing import Callable, Optional, Dict
import numpy as np
import cv2
from ..theme import COLORS
from ..corner_selector import CornerSelector
from ..overlay_selector import show_overlay_selector


class CalibrationTab:
    """Calibration tab for screen region selection and OCR detection testing."""

    def __init__(
        self,
        config,
        on_capture: Callable[[], np.ndarray],
        on_capture_region: Callable[[Dict], np.ndarray],
        on_test_detection: Callable[[np.ndarray], tuple],
        on_save_region: Callable[[Dict], None],
    ):
        self.config = config
        self.on_capture = on_capture
        self.on_capture_region = on_capture_region
        self.on_test_detection = on_test_detection
        self.on_save_region = on_save_region
        self._captured_frame: Optional[np.ndarray] = None
        self._corner_selector: Optional[CornerSelector] = None
        self._preview_texture_id: Optional[int] = None
        self._preview_size = (320, 180)  # Preview dimensions

        # Thread-safe pending updates (DearPyGui is not thread-safe)
        self._pending_progress: Optional[tuple[str, int]] = None
        self._pending_region: Optional[Dict] = None

        # Live debug mode
        self._live_debug_active = False
        self._live_debug_counter = 0

    def create(self, parent: int):
        """Create the Calibration tab content."""
        with dpg.tab(label="Calibration", parent=parent):
            # Screen region section
            dpg.add_text("Screen Region", color=COLORS['text_dim'])

            # Region display and select button
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Select Region",
                    callback=self._on_select_region_visual,
                    width=110
                )
                dpg.add_button(
                    label="F9 Mode",
                    callback=self._on_select_region_f9,
                    width=70
                )
                dpg.add_button(label="Clear", callback=self._on_clear_region, width=50)

            # Region info display
            self._update_region_display_init()

            # Status/instruction text (hidden by default)
            dpg.add_text(
                "",
                tag="f9_instruction",
                color=COLORS['accent'],
                wrap=280
            )

            dpg.add_separator()

            # Test section with visual debug
            dpg.add_text("Test Detection", color=COLORS['text_dim'])

            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Capture & Test",
                    callback=self._on_capture_and_test,
                    width=110
                )
                dpg.add_button(
                    label="Live Preview",
                    callback=self._on_toggle_live_preview,
                    width=90,
                    tag="live_preview_btn"
                )

            # Detection results
            dpg.add_text("Result: -", tag="detection_result", color=COLORS['text_dim'])

            # Visual preview area
            dpg.add_separator()
            dpg.add_text("Preview", color=COLORS['text_dim'])

            # Create preview texture placeholder
            self._create_preview_texture()

            # Preview image
            with dpg.drawlist(
                tag="preview_drawlist",
                width=self._preview_size[0],
                height=self._preview_size[1]
            ):
                dpg.draw_image(
                    self._preview_texture_id,
                    pmin=(0, 0),
                    pmax=self._preview_size,
                    tag="preview_image"
                )

            # Detection details
            dpg.add_text("", tag="detection_details", color=COLORS['text_secondary'], wrap=300)

    def _update_region_display_init(self):
        """Initialize region display text."""
        window_name = self.config.get('detection.region.window_name', '')

        if window_name:
            # Window-relative region
            w_pct = self.config.get('detection.region.w_percent', 0)
            h_pct = self.config.get('detection.region.h_percent', 0)
            x_pct = self.config.get('detection.region.x_percent', 0)
            y_pct = self.config.get('detection.region.y_percent', 0)

            if w_pct > 0 and h_pct > 0:
                region_text = f"Window: {window_name}\nRegion: {x_pct*100:.0f}%,{y_pct*100:.0f}% - {w_pct*100:.0f}%x{h_pct*100:.0f}%"
            else:
                region_text = f"Window: {window_name} (no region)"
        else:
            # Legacy absolute region
            region_x = self.config.get('detection.region.x', 0)
            region_y = self.config.get('detection.region.y', 0)
            region_w = self.config.get('detection.region.width', 0)
            region_h = self.config.get('detection.region.height', 0)

            if region_w > 0 and region_h > 0:
                region_text = f"Absolute: {region_x},{region_y} - {region_w}x{region_h}"
            else:
                region_text = "Full screen (no region set)"

        dpg.add_text(region_text, tag="region_display", color=COLORS['text_secondary'], wrap=280)

    def _update_region_display(self):
        """Update region display text."""
        window_name = self.config.get('detection.region.window_name', '')

        if window_name:
            w_pct = self.config.get('detection.region.w_percent', 0)
            h_pct = self.config.get('detection.region.h_percent', 0)
            x_pct = self.config.get('detection.region.x_percent', 0)
            y_pct = self.config.get('detection.region.y_percent', 0)

            if w_pct > 0 and h_pct > 0:
                text = f"Window: {window_name}\nRegion: {x_pct*100:.0f}%,{y_pct*100:.0f}% - {w_pct*100:.0f}%x{h_pct*100:.0f}%"
            else:
                text = f"Window: {window_name} (no region)"
        else:
            region = self._get_region()
            if region['width'] > 0 and region['height'] > 0:
                text = f"Absolute: {region['x']},{region['y']} - {region['width']}x{region['height']}"
            else:
                text = "Full screen (no region set)"

        if dpg.does_item_exist("region_display"):
            dpg.set_value("region_display", text)

    def _get_region(self) -> Dict:
        """Get current region from config (legacy format)."""
        return {
            'x': self.config.get('detection.region.x', 0),
            'y': self.config.get('detection.region.y', 0),
            'width': self.config.get('detection.region.width', 0),
            'height': self.config.get('detection.region.height', 0),
        }

    def _get_region_for_capture(self) -> Dict:
        """Get region dict suitable for capture (supports both formats)."""
        window_name = self.config.get('detection.region.window_name', '')

        if window_name:
            return {
                'window_name': window_name,
                'x_percent': self.config.get('detection.region.x_percent', 0),
                'y_percent': self.config.get('detection.region.y_percent', 0),
                'w_percent': self.config.get('detection.region.w_percent', 0),
                'h_percent': self.config.get('detection.region.h_percent', 0),
            }
        else:
            return self._get_region()

    def _create_preview_texture(self):
        """Create placeholder texture for preview."""
        w, h = self._preview_size
        # Dark gray placeholder
        placeholder = np.full((h, w, 4), 40, dtype=np.float32) / 255.0
        placeholder_flat = placeholder.flatten()

        with dpg.texture_registry():
            self._preview_texture_id = dpg.add_dynamic_texture(
                width=w,
                height=h,
                default_value=placeholder_flat.tolist(),
                tag="preview_texture"
            )

    def _update_preview(self, frame: np.ndarray):
        """Update preview texture with captured frame."""
        if frame is None or not dpg.does_item_exist("preview_texture"):
            return

        w, h = self._preview_size

        # Resize frame to preview size
        frame_resized = cv2.resize(frame, (w, h))

        # Convert to RGBA float
        if len(frame_resized.shape) == 2:
            frame_rgba = cv2.cvtColor(frame_resized, cv2.COLOR_GRAY2RGBA)
        elif frame_resized.shape[2] == 3:
            frame_rgba = cv2.cvtColor(frame_resized, cv2.COLOR_RGB2RGBA)
        else:
            frame_rgba = frame_resized

        # Normalize to 0-1
        frame_flat = frame_rgba.flatten().astype(np.float32) / 255.0

        dpg.set_value("preview_texture", frame_flat.tolist())

    def _on_select_region_visual(self):
        """Start visual overlay region selection (draw rectangle with mouse)."""
        # Show instruction
        if dpg.does_item_exist("f9_instruction"):
            dpg.set_value("f9_instruction", "Opening visual selector...")

        # Start overlay selector in a separate thread
        show_overlay_selector(
            on_complete=self._on_region_selected_visual,
            on_cancel=self._on_region_cancel_visual,
            run_in_thread=True
        )

    def _on_region_selected_visual(self, region: dict):
        """Handle region selection from visual overlay (called from background thread)."""
        # Queue for main thread processing (same as F9 method)
        self._pending_region = region

    def _on_region_cancel_visual(self):
        """Handle visual region selection cancel (called from background thread)."""
        self._pending_progress = ("", -1)

    def _on_select_region_f9(self):
        """Start F9 corner-click region selection (legacy mode)."""
        # Show instruction
        if dpg.does_item_exist("f9_instruction"):
            dpg.set_value("f9_instruction", "Move cursor to TOP-LEFT corner and press F9...")

        # Create and start corner selector
        self._corner_selector = CornerSelector(
            on_complete=self._on_region_selected_f9,
            on_cancel=self._on_region_cancel_f9,
            on_progress=self._on_region_progress
        )
        self._corner_selector.start()

    def on_f9_pressed(self):
        """Handle F9 hotkey press from main app."""
        if self._corner_selector and self._corner_selector.is_active:
            self._corner_selector.on_f9_pressed()

    def update(self):
        """Process pending updates from background threads. Call from main loop."""
        # Process pending progress update
        if self._pending_progress is not None:
            message, step = self._pending_progress
            self._pending_progress = None

            if dpg.does_item_exist("f9_instruction"):
                if step == -1 or step == 2:
                    dpg.set_value("f9_instruction", "")
                else:
                    dpg.set_value("f9_instruction", message)

        # Process pending region selection
        if self._pending_region is not None:
            region = self._pending_region
            self._pending_region = None

            self.on_save_region(region)
            self._update_region_display()

            if dpg.does_item_exist("f9_instruction"):
                dpg.set_value("f9_instruction", "")

            # Auto-capture and test
            self._on_capture_and_test()

        # Live debug mode - update every 10 frames (~6 FPS at 60 FPS main loop)
        if self._live_debug_active:
            self._live_debug_counter += 1
            if self._live_debug_counter >= 10:
                self._live_debug_counter = 0
                self._update_live_debug()

    def _on_region_progress(self, message: str, step: int):
        """Handle progress updates from corner selector (called from background thread)."""
        # Queue for main thread processing
        self._pending_progress = (message, step)

    def _on_region_selected_f9(self, region: Dict):
        """Handle region selection from F9 selector (called from background thread)."""
        # Queue for main thread processing
        self._pending_region = region

    def _on_region_cancel_f9(self):
        """Handle F9 region selection cancel (called from background thread)."""
        self._pending_progress = ("", -1)

    def _on_clear_region(self):
        """Clear the selected region (use full screen)."""
        region = {'x': 0, 'y': 0, 'width': 0, 'height': 0}
        self.on_save_region(region)
        self._update_region_display()

    def _on_capture_and_test(self):
        """Capture region and test detection with visual feedback."""
        region = self._get_region_for_capture()
        frame = self.on_capture_region(region)

        if frame is None:
            if dpg.does_item_exist("detection_result"):
                dpg.set_value("detection_result", "Result: Capture failed")
                dpg.configure_item("detection_result", color=COLORS['red'])
            return

        self._captured_frame = frame

        # Update preview
        self._update_preview(frame)

        # Test detection
        is_match, confidence = self.on_test_detection(frame)

        # Update result display
        if dpg.does_item_exist("detection_result"):
            if is_match:
                dpg.set_value("detection_result", f"MATCH ({confidence:.2f})")
                dpg.configure_item("detection_result", color=COLORS['green'])
            else:
                dpg.set_value("detection_result", f"No match ({confidence:.2f})")
                dpg.configure_item("detection_result", color=COLORS['red'])

        # Update details
        h, w = frame.shape[:2]
        current_game = self.config.get('current_game', 'Bloodborne')
        details = f"Frame: {w}x{h} | Game: {current_game}"

        if dpg.does_item_exist("detection_details"):
            dpg.set_value("detection_details", details)

    def _on_toggle_live_preview(self):
        """Toggle live preview mode."""
        self._live_debug_active = not self._live_debug_active

        if dpg.does_item_exist("live_preview_btn"):
            if self._live_debug_active:
                dpg.configure_item("live_preview_btn", label="Stop Debug")
                dpg.set_value("detection_result", "Live Debug: ON")
                dpg.configure_item("detection_result", color=COLORS['accent'])
            else:
                dpg.configure_item("live_preview_btn", label="Live Debug")
                dpg.set_value("detection_result", "Live Debug: OFF")
                dpg.configure_item("detection_result", color=COLORS['text_dim'])

    def _update_live_debug(self):
        """Update live debug preview with current capture and detection."""
        try:
            region = self._get_region_for_capture()
            frame = self.on_capture_region(region)

            if frame is None:
                return

            # Update preview
            self._update_preview(frame)

            # Test detection and get debug info
            is_match, _ = self.on_test_detection(frame)

            # Try to get OCR text for debugging
            ocr_text = ""
            try:
                import pytesseract
                from PIL import Image
                if len(frame.shape) == 3:
                    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                else:
                    gray = frame
                _, thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV)
                pil_img = Image.fromarray(thresh)
                ocr_text = pytesseract.image_to_string(pil_img, config="--oem 3 --psm 6").strip()
                ocr_text = ocr_text.replace('\n', ' ')[:60]
            except Exception:
                ocr_text = "(OCR error)"

            # Update result display
            if dpg.does_item_exist("detection_result"):
                if is_match:
                    dpg.set_value("detection_result", f"🔴 MATCH!")
                    dpg.configure_item("detection_result", color=COLORS['green'])
                else:
                    dpg.set_value("detection_result", f"⚪ No match")
                    dpg.configure_item("detection_result", color=COLORS['text_secondary'])

            # Update details with OCR text
            h, w = frame.shape[:2]
            details = f"OCR: \"{ocr_text}\"\nFrame: {w}x{h}"

            if dpg.does_item_exist("detection_details"):
                dpg.set_value("detection_details", details)

        except Exception as e:
            print(f"[LiveDebug] Error: {e}", flush=True)
