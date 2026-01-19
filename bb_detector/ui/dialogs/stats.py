# bb_detector/ui/dialogs/stats.py
"""Character stats add dialog."""
import dearpygui.dearpygui as dpg
from typing import Callable
from ..theme import COLORS, create_accent_button_theme


class StatsDialog:
    """Modal dialog for adding character stats."""

    def __init__(self, on_add: Callable[[dict], None], on_cancel: Callable[[], None] = None):
        self.on_add = on_add
        self.on_cancel = on_cancel or (lambda: None)
        self._accent_theme = None

    def show(self):
        """Show the stats dialog."""
        self._accent_theme = create_accent_button_theme()

        vp_width = dpg.get_viewport_width()
        vp_height = dpg.get_viewport_height()

        with dpg.window(
            label="Add Character Stats",
            tag="stats_dialog",
            modal=True,
            width=300,
            height=180,
            pos=[(vp_width - 300) // 2, (vp_height - 180) // 2],
            no_resize=True,
            on_close=self._on_cancel
        ):
            dpg.add_spacer(height=5)

            # Level
            with dpg.group(horizontal=True):
                dpg.add_text("Level", color=COLORS['text_tertiary'], indent=5)
                dpg.add_input_int(tag="stats_level", default_value=10, width=80, min_value=1, max_value=544)

            dpg.add_spacer(height=5)

            # Stats row 1: VIT, END, STR
            with dpg.group(horizontal=True):
                dpg.add_text("VIT", color=COLORS['text_tertiary'], indent=5)
                dpg.add_input_int(tag="stats_vit", default_value=10, width=50, min_value=1, max_value=99)
                dpg.add_text("END", color=COLORS['text_tertiary'])
                dpg.add_input_int(tag="stats_end", default_value=10, width=50, min_value=1, max_value=99)
                dpg.add_text("STR", color=COLORS['text_tertiary'])
                dpg.add_input_int(tag="stats_str", default_value=10, width=50, min_value=1, max_value=99)

            dpg.add_spacer(height=5)

            # Stats row 2: SKL, BLT, ARC
            with dpg.group(horizontal=True):
                dpg.add_text("SKL", color=COLORS['text_tertiary'], indent=5)
                dpg.add_input_int(tag="stats_skl", default_value=10, width=50, min_value=1, max_value=99)
                dpg.add_text("BLT", color=COLORS['text_tertiary'])
                dpg.add_input_int(tag="stats_blt", default_value=10, width=50, min_value=1, max_value=99)
                dpg.add_text("ARC", color=COLORS['text_tertiary'])
                dpg.add_input_int(tag="stats_arc", default_value=10, width=50, min_value=1, max_value=99)

            dpg.add_spacer(height=10)

            # Buttons
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=100)
                dpg.add_button(label="Cancel", width=80, callback=self._on_cancel)
                btn = dpg.add_button(label="Add", width=80, callback=self._on_add)
                dpg.bind_item_theme(btn, self._accent_theme)

    def _on_add(self, sender=None, app_data=None):
        """Handle add button."""
        stats = {
            'level': dpg.get_value("stats_level") if dpg.does_item_exist("stats_level") else 10,
            'vitality': dpg.get_value("stats_vit") if dpg.does_item_exist("stats_vit") else 10,
            'endurance': dpg.get_value("stats_end") if dpg.does_item_exist("stats_end") else 10,
            'strength': dpg.get_value("stats_str") if dpg.does_item_exist("stats_str") else 10,
            'skill': dpg.get_value("stats_skl") if dpg.does_item_exist("stats_skl") else 10,
            'bloodtinge': dpg.get_value("stats_blt") if dpg.does_item_exist("stats_blt") else 10,
            'arcane': dpg.get_value("stats_arc") if dpg.does_item_exist("stats_arc") else 10,
        }

        self._close()
        self.on_add(stats)

    def _on_cancel(self):
        """Handle cancel."""
        self._close()
        self.on_cancel()

    def _close(self):
        """Close dialog."""
        if dpg.does_item_exist("stats_dialog"):
            dpg.delete_item("stats_dialog")
