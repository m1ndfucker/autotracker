# bb_detector/ui/sections/setup.py
"""Setup section - merged settings + calibration functionality."""
import dearpygui.dearpygui as dpg
from typing import Callable, Optional, Dict, Any, List
import numpy as np
import cv2
import mss

from ..theme import COLORS, create_card_theme
from ..corner_selector import CornerSelector
from ..overlay_selector import show_overlay_selector


def _get_monitor_list() -> List[str]:
    """Get list of available monitors."""
    with mss.mss() as sct:
        # mss monitors[0] is "all monitors combined", skip it
        count = len(sct.monitors) - 1
        return [f"Display {i+1}" for i in range(count)]


class SetupSection:
    """Setup section with detection region, preview, settings, and hotkeys."""

    def __init__(
        self,
        config: Any,
        on_capture: Callable[[], np.ndarray],
        on_capture_region: Callable[[Dict], np.ndarray],
        on_test_detection: Callable[[np.ndarray], tuple],
        on_save_region: Callable[[Dict], None],
        on_save_settings: Callable[[Dict], None],
    ):
        self.config = config
        self.on_capture = on_capture
        self.on_capture_region = on_capture_region
        self.on_test_detection = on_test_detection
        self.on_save_region = on_save_region
        self.on_save_settings = on_save_settings

        self._captured_frame: Optional[np.ndarray] = None
        self._corner_selector: Optional[CornerSelector] = None
        self._preview_texture_id: Optional[int] = None
        self._preview_size = (180, 100)  # Preview dimensions

        # Thread-safe pending updates (DearPyGui is not thread-safe)
        self._pending_progress: Optional[tuple[str, int]] = None
        self._pending_region: Optional[Dict] = None

        # Live debug mode
        self._live_debug_active = False
        self._live_debug_counter = 0

        # Hotkey recording
        self._recording_hotkey: str = None

        # Card theme
        self._card_theme = None

        # Container tag
        self._container_tag = "setup_section_container"

    def create(self, parent: str):
        """Create the Setup section content."""
        # Create card theme
        self._card_theme = create_card_theme()

        # Create preview texture first
        self._create_preview_texture()

        with dpg.group(
            tag=self._container_tag,
            parent=parent
        ):
            # === Detection Region Card ===
            with dpg.child_window(height=75, border=True) as card1:
                dpg.bind_item_theme(card1, self._card_theme)

                dpg.add_text("DETECTION REGION", color=COLORS['text_tertiary'])
                dpg.add_spacer(height=4)

                # Region info display
                self._create_region_display()

                dpg.add_spacer(height=6)

                # Buttons row
                with dpg.group(horizontal=True):
                    dpg.add_button(
                        label="Select",
                        callback=self._on_select_region_visual,
                        width=60
                    )
                    dpg.add_button(
                        label="F9",
                        callback=self._on_select_region_f9,
                        width=40
                    )
                    dpg.add_button(
                        label="Clear",
                        callback=self._on_clear_region,
                        width=50
                    )

                # Status text (for F9 instructions)
                dpg.add_text(
                    "",
                    tag="setup_f9_instruction",
                    color=COLORS['accent'],
                    wrap=180
                )

            dpg.add_spacer(height=5)

            # === Test & Preview Card ===
            with dpg.child_window(height=140, border=True) as card2:
                dpg.bind_item_theme(card2, self._card_theme)

                dpg.add_text("TEST & PREVIEW", color=COLORS['text_tertiary'])
                dpg.add_spacer(height=4)

                with dpg.group(horizontal=True):
                    # Left: Preview image
                    with dpg.group():
                        with dpg.drawlist(
                            tag="setup_preview_drawlist",
                            width=self._preview_size[0],
                            height=self._preview_size[1]
                        ):
                            dpg.draw_image(
                                self._preview_texture_id,
                                pmin=(0, 0),
                                pmax=self._preview_size,
                                tag="setup_preview_image"
                            )

                    dpg.add_spacer(width=8)

                    # Right: Buttons and result
                    with dpg.group():
                        dpg.add_button(
                            label="Capture & Test",
                            callback=self._on_capture_and_test,
                            width=100
                        )
                        dpg.add_spacer(height=4)
                        dpg.add_button(
                            label="Live Preview",
                            callback=self._on_toggle_live_preview,
                            width=100,
                            tag="setup_live_preview_btn"
                        )
                        dpg.add_spacer(height=8)
                        dpg.add_text(
                            "Result: -",
                            tag="setup_detection_result",
                            color=COLORS['text_dim']
                        )

                # Detection details
                dpg.add_text(
                    "",
                    tag="setup_detection_details",
                    color=COLORS['text_secondary'],
                    wrap=190
                )

            dpg.add_spacer(height=5)

            # === Detection Settings Card ===
            with dpg.child_window(height=75, border=True) as card3:
                dpg.bind_item_theme(card3, self._card_theme)

                dpg.add_text("DETECTION SETTINGS", color=COLORS['text_tertiary'])
                dpg.add_spacer(height=4)

                # Monitor selection
                monitors = _get_monitor_list()
                with dpg.group(horizontal=True):
                    dpg.add_text("Monitor:", color=COLORS['text_dim'])
                    dpg.add_combo(
                        items=monitors if monitors else ["Display 1"],
                        default_value=monitors[0] if monitors else "Display 1",
                        tag="setup_monitor",
                        width=100,
                        callback=self._on_setting_change
                    )

                # Game selection
                with dpg.group(horizontal=True):
                    dpg.add_text("Game:", color=COLORS['text_dim'])
                    dpg.add_combo(
                        items=["Bloodborne", "Dark Souls", "Elden Ring", "Sekiro"],
                        default_value="Bloodborne",
                        tag="setup_game",
                        width=100,
                        callback=self._on_setting_change
                    )

                # Cooldown selection
                with dpg.group(horizontal=True):
                    dpg.add_text("Cooldown:", color=COLORS['text_dim'])
                    dpg.add_combo(
                        items=["3 sec", "5 sec", "10 sec"],
                        default_value="5 sec",
                        tag="setup_cooldown",
                        width=100,
                        callback=self._on_setting_change
                    )

            dpg.add_spacer(height=5)

            # === Hotkeys Card ===
            with dpg.child_window(height=95, border=True) as card4:
                dpg.bind_item_theme(card4, self._card_theme)

                dpg.add_text("HOTKEYS", color=COLORS['text_tertiary'])
                dpg.add_spacer(height=4)

                hotkeys = [
                    ("Manual Death:", "setup_hotkey_death", "Ctrl+Shift+D"),
                    ("Toggle Boss:", "setup_hotkey_boss", "Ctrl+Shift+B"),
                    ("Toggle Mode:", "setup_hotkey_mode", "Ctrl+Shift+O"),
                    ("Pause Detect:", "setup_hotkey_detect", "Ctrl+Shift+P"),
                ]

                for label, tag, default in hotkeys:
                    with dpg.group(horizontal=True):
                        dpg.add_text(label, color=COLORS['text_dim'])
                        dpg.add_button(
                            label=default,
                            tag=tag,
                            width=110,
                            callback=lambda s, a, u: self._start_hotkey_recording(u),
                            user_data=tag
                        )

    def _create_region_display(self):
        """Create region display text based on current config."""
        window_name = self.config.get('detection.region.window_name', '')

        if window_name:
            w_pct = self.config.get('detection.region.w_percent', 0)
            h_pct = self.config.get('detection.region.h_percent', 0)
            x_pct = self.config.get('detection.region.x_percent', 0)
            y_pct = self.config.get('detection.region.y_percent', 0)

            if w_pct > 0 and h_pct > 0:
                region_text = f"{window_name}\n{x_pct*100:.0f}%,{y_pct*100:.0f}% - {w_pct*100:.0f}%x{h_pct*100:.0f}%"
            else:
                region_text = f"{window_name} (no region)"
        else:
            region_x = self.config.get('detection.region.x', 0)
            region_y = self.config.get('detection.region.y', 0)
            region_w = self.config.get('detection.region.width', 0)
            region_h = self.config.get('detection.region.height', 0)

            if region_w > 0 and region_h > 0:
                region_text = f"Absolute: {region_x},{region_y} - {region_w}x{region_h}"
            else:
                region_text = "Full screen (no region set)"

        dpg.add_text(region_text, tag="setup_region_display", color=COLORS['text_secondary'], wrap=180)

    def _update_region_display(self):
        """Update region display text."""
        window_name = self.config.get('detection.region.window_name', '')

        if window_name:
            w_pct = self.config.get('detection.region.w_percent', 0)
            h_pct = self.config.get('detection.region.h_percent', 0)
            x_pct = self.config.get('detection.region.x_percent', 0)
            y_pct = self.config.get('detection.region.y_percent', 0)

            if w_pct > 0 and h_pct > 0:
                text = f"{window_name}\n{x_pct*100:.0f}%,{y_pct*100:.0f}% - {w_pct*100:.0f}%x{h_pct*100:.0f}%"
            else:
                text = f"{window_name} (no region)"
        else:
            region = self._get_region()
            if region['width'] > 0 and region['height'] > 0:
                text = f"Absolute: {region['x']},{region['y']} - {region['width']}x{region['height']}"
            else:
                text = "Full screen (no region set)"

        if dpg.does_item_exist("setup_region_display"):
            dpg.set_value("setup_region_display", text)

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
                tag="setup_preview_texture"
            )

    def _update_preview(self, frame: np.ndarray):
        """Update preview texture with captured frame."""
        if frame is None or not dpg.does_item_exist("setup_preview_texture"):
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

        dpg.set_value("setup_preview_texture", frame_flat.tolist())

    # === Region Selection ===

    def _on_select_region_visual(self):
        """Start visual overlay region selection."""
        if dpg.does_item_exist("setup_f9_instruction"):
            dpg.set_value("setup_f9_instruction", "Opening selector...")

        show_overlay_selector(
            on_complete=self._on_region_selected,
            on_cancel=self._on_region_cancel,
            run_in_thread=True
        )

    def _on_select_region_f9(self):
        """Start F9 corner-click region selection."""
        if dpg.does_item_exist("setup_f9_instruction"):
            dpg.set_value("setup_f9_instruction", "Move to TOP-LEFT, press F9...")

        self._corner_selector = CornerSelector(
            on_complete=self._on_region_selected,
            on_cancel=self._on_region_cancel,
            on_progress=self._on_region_progress
        )
        self._corner_selector.start()

    def on_f9_pressed(self):
        """Handle F9 hotkey press from main app."""
        if self._corner_selector and self._corner_selector.is_active:
            self._corner_selector.on_f9_pressed()

    def _on_region_progress(self, message: str, step: int):
        """Handle progress updates from corner selector (background thread)."""
        self._pending_progress = (message, step)

    def _on_region_selected(self, region: Dict):
        """Handle region selection (background thread)."""
        self._pending_region = region

    def _on_region_cancel(self):
        """Handle region selection cancel (background thread)."""
        self._pending_progress = ("", -1)

    def _on_clear_region(self):
        """Clear the selected region."""
        region = {'x': 0, 'y': 0, 'width': 0, 'height': 0}
        self.on_save_region(region)
        self._update_region_display()

    # === Test & Preview ===

    def _on_capture_and_test(self):
        """Capture region and test detection."""
        region = self._get_region_for_capture()
        frame = self.on_capture_region(region)

        if frame is None:
            if dpg.does_item_exist("setup_detection_result"):
                dpg.set_value("setup_detection_result", "Capture failed")
                dpg.configure_item("setup_detection_result", color=COLORS['red'])
            return

        self._captured_frame = frame
        self._update_preview(frame)

        # Test detection
        is_match, confidence = self.on_test_detection(frame)

        if dpg.does_item_exist("setup_detection_result"):
            if is_match:
                dpg.set_value("setup_detection_result", f"MATCH ({confidence:.2f})")
                dpg.configure_item("setup_detection_result", color=COLORS['green'])
            else:
                dpg.set_value("setup_detection_result", f"No match ({confidence:.2f})")
                dpg.configure_item("setup_detection_result", color=COLORS['red'])

        # Update details
        h, w = frame.shape[:2]
        current_game = self.config.get('current_game', 'Bloodborne')
        details = f"Frame: {w}x{h} | Game: {current_game}"

        if dpg.does_item_exist("setup_detection_details"):
            dpg.set_value("setup_detection_details", details)

    def _on_toggle_live_preview(self):
        """Toggle live preview mode."""
        self._live_debug_active = not self._live_debug_active

        if dpg.does_item_exist("setup_live_preview_btn"):
            if self._live_debug_active:
                dpg.configure_item("setup_live_preview_btn", label="Stop Preview")
                dpg.set_value("setup_detection_result", "Live: ON")
                dpg.configure_item("setup_detection_result", color=COLORS['accent'])
            else:
                dpg.configure_item("setup_live_preview_btn", label="Live Preview")
                dpg.set_value("setup_detection_result", "Live: OFF")
                dpg.configure_item("setup_detection_result", color=COLORS['text_dim'])

    def _update_live_debug(self):
        """Update live debug preview."""
        try:
            region = self._get_region_for_capture()
            frame = self.on_capture_region(region)

            if frame is None:
                return

            self._update_preview(frame)

            # Test detection
            is_match, _ = self.on_test_detection(frame)

            # Try to get OCR text
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
                ocr_text = ocr_text.replace('\n', ' ')[:40]
            except Exception:
                ocr_text = "(OCR error)"

            if dpg.does_item_exist("setup_detection_result"):
                if is_match:
                    dpg.set_value("setup_detection_result", "MATCH!")
                    dpg.configure_item("setup_detection_result", color=COLORS['green'])
                else:
                    dpg.set_value("setup_detection_result", "No match")
                    dpg.configure_item("setup_detection_result", color=COLORS['text_secondary'])

            if dpg.does_item_exist("setup_detection_details"):
                h, w = frame.shape[:2]
                details = f"OCR: \"{ocr_text}\"\n{w}x{h}"
                dpg.set_value("setup_detection_details", details)

        except Exception as e:
            print(f"[SetupSection] Live debug error: {e}", flush=True)

    # === Settings ===

    def _on_setting_change(self, sender, app_data):
        """Handle setting change."""
        settings = self._collect_settings()
        self.on_save_settings(settings)

    def _collect_settings(self) -> Dict:
        """Collect all settings values."""
        settings = {}

        if dpg.does_item_exist("setup_monitor"):
            val = dpg.get_value("setup_monitor")
            settings['detection.monitor'] = int(val.split()[-1]) - 1

        if dpg.does_item_exist("setup_game"):
            settings['current_game'] = dpg.get_value("setup_game")

        if dpg.does_item_exist("setup_cooldown"):
            val = dpg.get_value("setup_cooldown")
            settings['detection.death_cooldown'] = float(val.split()[0])

        return settings

    def load_from_config(self):
        """Load settings from config."""
        if dpg.does_item_exist("setup_monitor"):
            monitor = self.config.get('detection.monitor', 0)
            dpg.set_value("setup_monitor", f"Display {monitor + 1}")

        if dpg.does_item_exist("setup_game"):
            game = self.config.get('current_game', 'Bloodborne')
            dpg.set_value("setup_game", game)

        if dpg.does_item_exist("setup_cooldown"):
            cooldown = self.config.get('detection.death_cooldown', 5.0)
            dpg.set_value("setup_cooldown", f"{int(cooldown)} sec")

    # === Hotkeys ===

    def _start_hotkey_recording(self, tag: str):
        """Start recording a hotkey."""
        self._recording_hotkey = tag
        if dpg.does_item_exist(tag):
            dpg.set_item_label(tag, "Press keys...")
        # TODO: Integrate with pynput for actual recording

    # === Update Loop ===

    def update(self):
        """Process pending updates from background threads. Call from main loop."""
        # Process pending progress update
        if self._pending_progress is not None:
            message, step = self._pending_progress
            self._pending_progress = None

            if dpg.does_item_exist("setup_f9_instruction"):
                if step == -1 or step == 2:
                    dpg.set_value("setup_f9_instruction", "")
                else:
                    dpg.set_value("setup_f9_instruction", message)

        # Process pending region selection
        if self._pending_region is not None:
            region = self._pending_region
            self._pending_region = None

            self.on_save_region(region)
            self._update_region_display()

            if dpg.does_item_exist("setup_f9_instruction"):
                dpg.set_value("setup_f9_instruction", "")

            # Auto-capture and test
            self._on_capture_and_test()

        # Live debug mode - update every 10 frames (~6 FPS at 60 FPS main loop)
        if self._live_debug_active:
            self._live_debug_counter += 1
            if self._live_debug_counter >= 10:
                self._live_debug_counter = 0
                self._update_live_debug()

    # === Show/Hide ===

    def show(self):
        """Show the section."""
        if dpg.does_item_exist(self._container_tag):
            dpg.show_item(self._container_tag)

    def hide(self):
        """Hide the section."""
        if dpg.does_item_exist(self._container_tag):
            dpg.hide_item(self._container_tag)
        # Stop live debug when hidden
        if self._live_debug_active:
            self._live_debug_active = False
            if dpg.does_item_exist("setup_live_preview_btn"):
                dpg.configure_item("setup_live_preview_btn", label="Live Preview")
