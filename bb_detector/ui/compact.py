# bb_detector/ui/compact.py
"""Compact mode window - minimal overlay during gameplay."""
import dearpygui.dearpygui as dpg
from typing import Callable
from .theme import COLORS

class CompactWindow:
    """Compact overlay window showing essential info during gameplay."""

    WIDTH = 300
    HEIGHT = 60

    def __init__(self, on_expand: Callable[[], None]):
        self.on_expand = on_expand
        self._visible = False
        self._position = [50, 50]

    def create(self):
        """Create the compact window (hidden initially)."""
        with dpg.window(
            tag="compact_window",
            label="BB Detector",
            width=self.WIDTH,
            height=self.HEIGHT,
            pos=self._position,
            no_title_bar=True,
            no_resize=True,
            no_scrollbar=True,
            no_collapse=True,
            show=False,
        ):
            with dpg.group(horizontal=True):
                # Deaths
                dpg.add_text("", tag="compact_deaths", color=COLORS['accent'])
                dpg.add_spacer(width=15)

                # Timer
                dpg.add_text("", tag="compact_timer")

            with dpg.group(horizontal=True):
                # Boss info
                dpg.add_text("", tag="compact_boss", color=COLORS['boss'])
                dpg.add_spacer(width=15)

                # Status
                dpg.add_text("", tag="compact_status", color=COLORS['success'])

        # Click handler to expand
        with dpg.item_handler_registry(tag="compact_click_handler"):
            dpg.add_item_clicked_handler(callback=self._on_click)

        dpg.bind_item_handler_registry("compact_window", "compact_click_handler")

    def show(self):
        """Show compact window."""
        if dpg.does_item_exist("compact_window"):
            dpg.configure_item("compact_window", show=True)
            self._visible = True

    def hide(self):
        """Hide compact window."""
        if dpg.does_item_exist("compact_window"):
            # Save position before hiding
            self._position = dpg.get_item_pos("compact_window")
            dpg.configure_item("compact_window", show=False)
            self._visible = False

    def is_visible(self) -> bool:
        return self._visible

    def update(self, deaths: int, elapsed: int, boss_mode: bool,
               boss_deaths: int, connected: bool, profile: str):
        """Update compact display."""
        # Deaths
        if dpg.does_item_exist("compact_deaths"):
            dpg.set_value("compact_deaths", f"Deaths: {deaths}")

        # Timer
        if dpg.does_item_exist("compact_timer"):
            hours = elapsed // 3600000
            minutes = (elapsed % 3600000) // 60000
            seconds = (elapsed % 60000) // 1000
            dpg.set_value("compact_timer", f"{hours:02d}:{minutes:02d}:{seconds:02d}")

        # Boss
        if dpg.does_item_exist("compact_boss"):
            if boss_mode:
                dpg.set_value("compact_boss", f"Boss: {boss_deaths}")
            else:
                dpg.set_value("compact_boss", "")

        # Status
        if dpg.does_item_exist("compact_status"):
            if connected:
                dpg.set_value("compact_status", f"{profile}")
                dpg.configure_item("compact_status", color=COLORS['success'])
            else:
                dpg.set_value("compact_status", "Offline")
                dpg.configure_item("compact_status", color=COLORS['accent'])

    def set_position(self, x: int, y: int):
        """Set window position."""
        self._position = [x, y]
        if dpg.does_item_exist("compact_window"):
            dpg.set_item_pos("compact_window", self._position)

    def get_position(self) -> list:
        """Get current window position."""
        if dpg.does_item_exist("compact_window"):
            return dpg.get_item_pos("compact_window")
        return self._position

    def _on_click(self, sender, app_data):
        """Handle click on compact window."""
        # Click to expand (app_data: 0=left, 1=right, 2=middle)
        if app_data == 0:  # Left click
            self.on_expand()
