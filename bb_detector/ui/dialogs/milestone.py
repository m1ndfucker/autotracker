# bb_detector/ui/dialogs/milestone.py
"""Milestone add dialog."""
import dearpygui.dearpygui as dpg
from typing import Callable
from ..theme import COLORS, create_accent_button_theme

MILESTONE_ICONS = ['★', '⚑', '♦', '▲', '●', '◆', '♠', '✦']


class MilestoneDialog:
    """Modal dialog for adding a milestone."""

    def __init__(self, on_add: Callable[[str, str], None], on_cancel: Callable[[], None] = None):
        self.on_add = on_add
        self.on_cancel = on_cancel or (lambda: None)
        self._accent_theme = None

    def show(self):
        """Show the milestone dialog."""
        self._accent_theme = create_accent_button_theme()

        vp_width = dpg.get_viewport_width()
        vp_height = dpg.get_viewport_height()

        with dpg.window(
            label="Add Milestone",
            tag="milestone_dialog",
            modal=True,
            width=250,
            height=120,
            pos=[(vp_width - 250) // 2, (vp_height - 120) // 2],
            no_resize=True,
            on_close=self._on_cancel
        ):
            dpg.add_spacer(height=5)

            with dpg.group(horizontal=True):
                dpg.add_input_text(
                    tag="milestone_name_input",
                    hint="Milestone name...",
                    width=170,
                    on_enter=True,
                    callback=self._on_add
                )
                dpg.add_combo(
                    MILESTONE_ICONS,
                    tag="milestone_icon_combo",
                    default_value='★',
                    width=50
                )

            dpg.add_spacer(height=10)

            with dpg.group(horizontal=True):
                dpg.add_spacer(width=60)
                dpg.add_button(label="Cancel", width=80, callback=self._on_cancel)
                btn = dpg.add_button(label="Add", width=80, callback=self._on_add)
                dpg.bind_item_theme(btn, self._accent_theme)

    def _on_add(self, sender=None, app_data=None):
        """Handle add button."""
        if not dpg.does_item_exist("milestone_name_input"):
            return

        name = dpg.get_value("milestone_name_input").strip()
        if not name:
            return

        icon = dpg.get_value("milestone_icon_combo") if dpg.does_item_exist("milestone_icon_combo") else '★'

        self._close()
        self.on_add(name, icon)

    def _on_cancel(self):
        """Handle cancel."""
        self._close()
        self.on_cancel()

    def _close(self):
        """Close dialog."""
        if dpg.does_item_exist("milestone_dialog"):
            dpg.delete_item("milestone_dialog")
