# bb_detector/ui/tabs/calibration.py
"""Calibration tab - template selection and detection testing."""
import dearpygui.dearpygui as dpg
from typing import Callable, Optional
from pathlib import Path
import numpy as np
from ..theme import COLORS


class CalibrationTab:
    """Calibration tab for template selection and detection testing."""

    TEMPLATES = [
        ("YOU DIED (English)", "you_died_en.png"),
        ("ТЫ МЕРТВ (Russian)", "you_died_ru.png"),
        ("Custom...", None),
    ]

    def __init__(
        self,
        on_template_change: Callable[[str], None],
        on_capture: Callable[[], np.ndarray],
        on_test_detection: Callable[[np.ndarray], tuple],
    ):
        self.on_template_change = on_template_change
        self.on_capture = on_capture
        self.on_test_detection = on_test_detection
        self._captured_frame: Optional[np.ndarray] = None
        self._texture_id: Optional[int] = None

    def create(self, parent: int):
        """Create the Calibration tab content."""
        with dpg.tab(label="Calibration", parent=parent):
            dpg.add_spacer(height=10)

            # Template section
            dpg.add_text("DEATH TEMPLATE", color=COLORS['text_dim'])
            dpg.add_spacer(height=5)

            # Template preview placeholder
            with dpg.child_window(height=80, border=True, tag="template_preview_window"):
                dpg.add_text("Template preview", color=COLORS['text_dim'])

            dpg.add_spacer(height=10)

            # Template selector
            with dpg.group(horizontal=True):
                dpg.add_text("Template:", color=COLORS['text_dim'])
                dpg.add_combo(
                    items=[t[0] for t in self.TEMPLATES],
                    default_value=self.TEMPLATES[0][0],
                    tag="template_selector",
                    width=200,
                    callback=self._on_template_select
                )

            dpg.add_spacer(height=15)
            dpg.add_separator()
            dpg.add_spacer(height=10)

            # Test detection section
            dpg.add_text("TEST DETECTION", color=COLORS['text_dim'])
            dpg.add_spacer(height=10)

            dpg.add_button(label="Capture Screen", callback=self._on_capture, width=150)

            dpg.add_spacer(height=10)

            # Captured frame preview
            with dpg.child_window(height=150, border=True, tag="capture_preview_window"):
                dpg.add_text("No capture", tag="capture_status", color=COLORS['text_dim'])
                dpg.add_spacer(height=10)
                dpg.add_text("Result: -", tag="detection_result", color=COLORS['text_dim'])

            dpg.add_spacer(height=10)

            with dpg.group(horizontal=True):
                dpg.add_button(label="Test Now", callback=self._on_test, width=100)
                dpg.add_button(label="Load Image", callback=self._on_load_image, width=100)

    def _on_template_select(self, sender, app_data):
        """Handle template selection."""
        selected = app_data

        # Find the template file
        template_file = None
        for name, file in self.TEMPLATES:
            if name == selected:
                template_file = file
                break

        if template_file is None:
            # Custom - open file dialog
            self._open_file_dialog()
        else:
            self.on_template_change(template_file)

    def _open_file_dialog(self):
        """Open file dialog for custom template."""
        # DearPyGui file dialog
        with dpg.file_dialog(
            directory_selector=False,
            show=True,
            callback=self._on_file_selected,
            width=500,
            height=400
        ):
            dpg.add_file_extension(".png")
            dpg.add_file_extension(".jpg")
            dpg.add_file_extension(".jpeg")

    def _on_file_selected(self, sender, app_data):
        """Handle custom file selection."""
        if app_data and 'file_path_name' in app_data:
            file_path = app_data['file_path_name']
            self.on_template_change(file_path)

    def _on_capture(self):
        """Capture current screen."""
        frame = self.on_capture()
        if frame is not None:
            self._captured_frame = frame
            self._update_capture_preview()

    def _update_capture_preview(self):
        """Update capture preview display."""
        if self._captured_frame is not None:
            if dpg.does_item_exist("capture_status"):
                h, w = self._captured_frame.shape[:2]
                dpg.set_value("capture_status", f"Captured: {w}x{h}")

    def _on_test(self):
        """Test detection on captured frame."""
        if self._captured_frame is None:
            if dpg.does_item_exist("detection_result"):
                dpg.set_value("detection_result", "Result: No capture to test")
            return

        is_match, confidence = self.on_test_detection(self._captured_frame)

        if dpg.does_item_exist("detection_result"):
            if is_match:
                dpg.set_value("detection_result", f"Result: MATCH ({confidence:.2f})")
                dpg.configure_item("detection_result", color=COLORS['success'])
            else:
                dpg.set_value("detection_result", f"Result: No match ({confidence:.2f})")
                dpg.configure_item("detection_result", color=COLORS['accent'])

    def _on_load_image(self):
        """Load image from file for testing."""
        with dpg.file_dialog(
            directory_selector=False,
            show=True,
            callback=self._on_test_image_selected,
            width=500,
            height=400
        ):
            dpg.add_file_extension(".png")
            dpg.add_file_extension(".jpg")
            dpg.add_file_extension(".jpeg")

    def _on_test_image_selected(self, sender, app_data):
        """Handle test image file selection."""
        if app_data and 'file_path_name' in app_data:
            import cv2
            file_path = app_data['file_path_name']
            frame = cv2.imread(file_path)
            if frame is not None:
                # Convert BGR to RGB
                self._captured_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self._update_capture_preview()
