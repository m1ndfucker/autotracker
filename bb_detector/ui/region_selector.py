# bb_detector/ui/region_selector.py
"""Visual region selection overlay."""
import dearpygui.dearpygui as dpg
import numpy as np
from typing import Callable, Optional
from .theme import COLORS


class RegionSelector:
    """Full-screen region selection with mouse drag."""

    def __init__(
        self,
        screenshot: np.ndarray,
        on_select: Callable[[dict], None],
        on_cancel: Callable[[], None],
    ):
        self.screenshot = screenshot
        self.on_select = on_select
        self.on_cancel = on_cancel

        self._texture_id: Optional[int] = None
        self._window_tag = "region_selector_window"
        self._drawlist_tag = "region_drawlist"

        # Selection state
        self._is_dragging = False
        self._start_x = 0
        self._start_y = 0
        self._end_x = 0
        self._end_y = 0

        # Image display scale (screenshot might be larger than window)
        self._scale = 1.0
        self._img_offset_x = 0
        self._img_offset_y = 40  # Account for header

    def show(self):
        """Show the region selector window."""
        img_h, img_w = self.screenshot.shape[:2]

        # Scale down if too large (max 1200x800)
        max_w, max_h = 1200, 800
        scale_w = max_w / img_w if img_w > max_w else 1.0
        scale_h = max_h / img_h if img_h > max_h else 1.0
        self._scale = min(scale_w, scale_h)

        display_w = int(img_w * self._scale)
        display_h = int(img_h * self._scale)

        # Create texture from screenshot
        self._create_texture(display_w, display_h)

        # Create window
        with dpg.window(
            label="Select Region - Drag to select area",
            tag=self._window_tag,
            width=display_w + 20,
            height=display_h + 80,
            modal=True,
            no_resize=True,
            on_close=self._on_cancel_click,
        ):
            dpg.add_text("Drag mouse to select detection region", color=COLORS['text_dim'])

            # Drawlist for image and selection rectangle
            with dpg.drawlist(
                tag=self._drawlist_tag,
                width=display_w,
                height=display_h,
            ):
                # Draw the screenshot
                dpg.draw_image(
                    self._texture_id,
                    pmin=(0, 0),
                    pmax=(display_w, display_h),
                )

            # Buttons
            with dpg.group(horizontal=True):
                dpg.add_button(label="Cancel", callback=self._on_cancel_click, width=100)
                dpg.add_button(label="Confirm", callback=self._on_confirm_click, width=100)
                dpg.add_text("", tag="region_info", color=COLORS['text_dim'])

        # Register mouse handlers
        with dpg.handler_registry(tag="region_mouse_handler"):
            dpg.add_mouse_click_handler(button=dpg.mvMouseButton_Left, callback=self._on_mouse_down)
            dpg.add_mouse_release_handler(button=dpg.mvMouseButton_Left, callback=self._on_mouse_up)
            dpg.add_mouse_move_handler(callback=self._on_mouse_move)

    def _create_texture(self, display_w: int, display_h: int):
        """Create DearPyGui texture from screenshot."""
        import cv2

        # Resize for display
        img_resized = cv2.resize(self.screenshot, (display_w, display_h))

        # Convert BGR to RGBA
        if len(img_resized.shape) == 2:
            img_rgba = cv2.cvtColor(img_resized, cv2.COLOR_GRAY2RGBA)
        elif img_resized.shape[2] == 3:
            img_rgba = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGBA)
        else:
            img_rgba = img_resized

        # Normalize to 0-1 float
        img_flat = img_rgba.flatten().astype(np.float32) / 255.0

        # Create texture
        with dpg.texture_registry():
            self._texture_id = dpg.add_static_texture(
                width=display_w,
                height=display_h,
                default_value=img_flat,
            )

    def _get_drawlist_mouse_pos(self):
        """Get mouse position relative to drawlist."""
        mouse_pos = dpg.get_mouse_pos(local=False)

        if not dpg.does_item_exist(self._drawlist_tag):
            return None, None

        # Get drawlist position in viewport
        dl_pos = dpg.get_item_pos(self._drawlist_tag)
        window_pos = dpg.get_item_pos(self._window_tag)

        # Calculate relative position
        rel_x = mouse_pos[0] - window_pos[0] - dl_pos[0]
        rel_y = mouse_pos[1] - window_pos[1] - dl_pos[1]

        return rel_x, rel_y

    def _on_mouse_down(self):
        """Handle mouse down - start selection."""
        if not dpg.does_item_exist(self._window_tag):
            return

        rel_x, rel_y = self._get_drawlist_mouse_pos()
        if rel_x is None:
            return

        # Check if within drawlist bounds
        dl_w = dpg.get_item_width(self._drawlist_tag)
        dl_h = dpg.get_item_height(self._drawlist_tag)

        if 0 <= rel_x <= dl_w and 0 <= rel_y <= dl_h:
            self._is_dragging = True
            self._start_x = rel_x
            self._start_y = rel_y
            self._end_x = rel_x
            self._end_y = rel_y

    def _on_mouse_move(self):
        """Handle mouse move - update selection."""
        if not self._is_dragging:
            return

        rel_x, rel_y = self._get_drawlist_mouse_pos()
        if rel_x is None:
            return

        # Clamp to drawlist bounds
        dl_w = dpg.get_item_width(self._drawlist_tag)
        dl_h = dpg.get_item_height(self._drawlist_tag)

        self._end_x = max(0, min(rel_x, dl_w))
        self._end_y = max(0, min(rel_y, dl_h))

        self._draw_selection()

    def _on_mouse_up(self):
        """Handle mouse up - finish selection."""
        if self._is_dragging:
            self._is_dragging = False
            self._draw_selection()

    def _draw_selection(self):
        """Draw selection rectangle on drawlist."""
        if not dpg.does_item_exist(self._drawlist_tag):
            return

        # Remove old selection rectangle
        if dpg.does_item_exist("selection_rect"):
            dpg.delete_item("selection_rect")
        if dpg.does_item_exist("selection_rect_border"):
            dpg.delete_item("selection_rect_border")

        # Calculate rectangle bounds
        x1 = min(self._start_x, self._end_x)
        y1 = min(self._start_y, self._end_y)
        x2 = max(self._start_x, self._end_x)
        y2 = max(self._start_y, self._end_y)

        if x2 - x1 > 5 and y2 - y1 > 5:
            # Draw semi-transparent fill
            dpg.draw_rectangle(
                pmin=(x1, y1),
                pmax=(x2, y2),
                color=(220, 68, 68, 80),
                fill=(220, 68, 68, 40),
                tag="selection_rect",
                parent=self._drawlist_tag,
            )
            # Draw border
            dpg.draw_rectangle(
                pmin=(x1, y1),
                pmax=(x2, y2),
                color=(220, 68, 68, 255),
                thickness=2,
                tag="selection_rect_border",
                parent=self._drawlist_tag,
            )

            # Update info text with actual screen coordinates
            screen_x = int(x1 / self._scale)
            screen_y = int(y1 / self._scale)
            screen_w = int((x2 - x1) / self._scale)
            screen_h = int((y2 - y1) / self._scale)

            if dpg.does_item_exist("region_info"):
                dpg.set_value("region_info", f"Region: {screen_x},{screen_y} {screen_w}x{screen_h}")

    def _on_confirm_click(self):
        """Confirm selection."""
        # Calculate actual screen coordinates
        x1 = min(self._start_x, self._end_x)
        y1 = min(self._start_y, self._end_y)
        x2 = max(self._start_x, self._end_x)
        y2 = max(self._start_y, self._end_y)

        screen_x = int(x1 / self._scale)
        screen_y = int(y1 / self._scale)
        screen_w = int((x2 - x1) / self._scale)
        screen_h = int((y2 - y1) / self._scale)

        region = {
            'x': screen_x,
            'y': screen_y,
            'width': screen_w,
            'height': screen_h,
        }

        self._cleanup()
        self.on_select(region)

    def _on_cancel_click(self):
        """Cancel selection."""
        self._cleanup()
        self.on_cancel()

    def _cleanup(self):
        """Clean up resources."""
        if dpg.does_item_exist("region_mouse_handler"):
            dpg.delete_item("region_mouse_handler")
        if dpg.does_item_exist(self._window_tag):
            dpg.delete_item(self._window_tag)
        if self._texture_id and dpg.does_item_exist(self._texture_id):
            dpg.delete_item(self._texture_id)
