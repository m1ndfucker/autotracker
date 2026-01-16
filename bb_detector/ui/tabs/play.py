"""Play tab - main gameplay controls."""
import dearpygui.dearpygui as dpg
from typing import Callable, Optional
from ..theme import COLORS, create_accent_button_theme, create_success_button_theme, create_boss_button_theme


class PlayTab:
    """Play tab with deaths, timer, and boss controls."""

    def __init__(
        self,
        on_manual_death: Callable[[], None],
        on_timer_start: Callable[[], None],
        on_timer_stop: Callable[[], None],
        on_timer_reset: Callable[[], None],
        on_boss_start: Callable[[], None],
        on_boss_victory: Callable[[str], None],
        on_boss_cancel: Callable[[], None],
        on_toggle_detection: Callable[[], None],
    ):
        self.on_manual_death = on_manual_death
        self.on_timer_start = on_timer_start
        self.on_timer_stop = on_timer_stop
        self.on_timer_reset = on_timer_reset
        self.on_boss_start = on_boss_start
        self.on_boss_victory = on_boss_victory
        self.on_boss_cancel = on_boss_cancel
        self.on_toggle_detection = on_toggle_detection

        self._accent_theme = None
        self._success_theme = None
        self._boss_theme = None

    def create(self, parent: int):
        """Create the Play tab content."""
        self._accent_theme = create_accent_button_theme()
        self._success_theme = create_success_button_theme()
        self._boss_theme = create_boss_button_theme()

        with dpg.tab(label="Play", parent=parent):
            dpg.add_spacer(height=10)

            # Deaths section
            dpg.add_text("DEATHS", color=COLORS['text_dim'])
            dpg.add_spacer(height=5)

            with dpg.child_window(height=80, border=True):
                dpg.add_spacer(height=10)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=20)
                    dpg.add_text("0", tag="deaths_display", color=COLORS['accent'])

                dpg.add_spacer(height=10)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=20)
                    btn = dpg.add_button(label="+ Manual Death", callback=self._on_death_click, width=150)
                    dpg.bind_item_theme(btn, self._accent_theme)

            dpg.add_spacer(height=15)

            # Timer section
            with dpg.group(horizontal=True):
                dpg.add_text("TIMER", color=COLORS['text_dim'])
                dpg.add_spacer(width=20)
                dpg.add_text("00:00:00", tag="timer_display")

            dpg.add_spacer(height=5)
            with dpg.group(horizontal=True):
                btn_start = dpg.add_button(label="Start", tag="timer_start_btn", callback=self._on_timer_start, width=80)
                dpg.bind_item_theme(btn_start, self._success_theme)
                btn_stop = dpg.add_button(label="Stop", tag="timer_stop_btn", callback=self._on_timer_stop, width=80)
                dpg.add_button(label="Reset", callback=self._on_timer_reset, width=80)

            dpg.add_spacer(height=15)
            dpg.add_separator()
            dpg.add_spacer(height=10)

            # Boss mode section
            with dpg.group(horizontal=True):
                dpg.add_text("BOSS MODE", color=COLORS['text_dim'])
                dpg.add_spacer(width=10)
                dpg.add_text("OFF", tag="boss_status", color=COLORS['text_dim'])

            dpg.add_spacer(height=5)

            with dpg.child_window(height=100, border=True, tag="boss_section"):
                dpg.add_spacer(height=5)

                with dpg.group(horizontal=True):
                    dpg.add_text("Boss Deaths:", color=COLORS['text_dim'])
                    dpg.add_text("0", tag="boss_deaths_display", color=COLORS['boss'])

                dpg.add_spacer(height=10)

                with dpg.group(horizontal=True, tag="boss_buttons_inactive"):
                    btn_boss = dpg.add_button(label="Start Boss", callback=self._on_boss_start, width=120)
                    dpg.bind_item_theme(btn_boss, self._boss_theme)

                with dpg.group(horizontal=True, tag="boss_buttons_active", show=False):
                    btn_victory = dpg.add_button(label="Victory", callback=self._on_boss_victory_click, width=100)
                    dpg.bind_item_theme(btn_victory, self._success_theme)
                    btn_cancel = dpg.add_button(label="Cancel", callback=self._on_boss_cancel, width=100)

            dpg.add_spacer(height=15)
            dpg.add_separator()
            dpg.add_spacer(height=10)

            # Detection toggle
            with dpg.group(horizontal=True):
                dpg.add_text("Detection:", color=COLORS['text_dim'])
                dpg.add_spacer(width=5)
                dpg.add_text("ON", tag="detection_status", color=COLORS['success'])
                dpg.add_spacer(width=20)
                dpg.add_button(label="Toggle", callback=self._on_toggle_detection, width=80)

    def update(self, deaths: int, elapsed: int, is_running: bool,
               boss_mode: bool, boss_deaths: int, detection_enabled: bool):
        """Update all displays."""
        # Deaths
        if dpg.does_item_exist("deaths_display"):
            dpg.set_value("deaths_display", str(deaths))

        # Timer
        if dpg.does_item_exist("timer_display"):
            hours = elapsed // 3600000
            minutes = (elapsed % 3600000) // 60000
            seconds = (elapsed % 60000) // 1000
            dpg.set_value("timer_display", f"{hours:02d}:{minutes:02d}:{seconds:02d}")

        # Timer buttons
        if dpg.does_item_exist("timer_start_btn"):
            dpg.configure_item("timer_start_btn", enabled=not is_running)
        if dpg.does_item_exist("timer_stop_btn"):
            dpg.configure_item("timer_stop_btn", enabled=is_running)

        # Boss mode
        if dpg.does_item_exist("boss_status"):
            if boss_mode:
                dpg.set_value("boss_status", "ACTIVE")
                dpg.configure_item("boss_status", color=COLORS['boss'])
            else:
                dpg.set_value("boss_status", "OFF")
                dpg.configure_item("boss_status", color=COLORS['text_dim'])

        if dpg.does_item_exist("boss_deaths_display"):
            dpg.set_value("boss_deaths_display", str(boss_deaths))

        if dpg.does_item_exist("boss_buttons_inactive"):
            dpg.configure_item("boss_buttons_inactive", show=not boss_mode)
        if dpg.does_item_exist("boss_buttons_active"):
            dpg.configure_item("boss_buttons_active", show=boss_mode)

        # Detection
        if dpg.does_item_exist("detection_status"):
            if detection_enabled:
                dpg.set_value("detection_status", "ON")
                dpg.configure_item("detection_status", color=COLORS['success'])
            else:
                dpg.set_value("detection_status", "OFF")
                dpg.configure_item("detection_status", color=COLORS['accent'])

    def _on_death_click(self):
        self.on_manual_death()

    def _on_timer_start(self):
        self.on_timer_start()

    def _on_timer_stop(self):
        self.on_timer_stop()

    def _on_timer_reset(self):
        self.on_timer_reset()

    def _on_boss_start(self):
        self.on_boss_start()

    def _on_boss_victory_click(self):
        """Show victory dialog to enter boss name."""
        with dpg.window(
            label="Boss Victory",
            modal=True,
            width=300,
            height=120,
            pos=[100, 200],
            tag="victory_dialog",
            no_resize=True
        ):
            dpg.add_text("Enter boss name:")
            dpg.add_input_text(tag="boss_name_input", width=-1)
            dpg.add_spacer(height=10)
            with dpg.group(horizontal=True):
                dpg.add_button(label="Cancel", callback=lambda: dpg.delete_item("victory_dialog"), width=100)
                dpg.add_button(label="Confirm", callback=self._on_victory_confirm, width=100)

    def _on_victory_confirm(self):
        name = dpg.get_value("boss_name_input") if dpg.does_item_exist("boss_name_input") else ""
        if dpg.does_item_exist("victory_dialog"):
            dpg.delete_item("victory_dialog")
        self.on_boss_victory(name)

    def _on_boss_cancel(self):
        self.on_boss_cancel()

    def _on_toggle_detection(self):
        self.on_toggle_detection()
