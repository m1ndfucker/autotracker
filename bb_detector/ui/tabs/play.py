# bb_detector/ui/tabs/play.py
"""Play tab - main gameplay controls."""
import dearpygui.dearpygui as dpg
from typing import Callable
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
        on_boss_pause: Callable[[], None],
        on_boss_resume: Callable[[], None],
        on_boss_victory: Callable[[str], None],
        on_boss_cancel: Callable[[], None],
        on_toggle_detection: Callable[[], None],
    ):
        self.on_manual_death = on_manual_death
        self.on_timer_start = on_timer_start
        self.on_timer_stop = on_timer_stop
        self.on_timer_reset = on_timer_reset
        self.on_boss_start = on_boss_start
        self.on_boss_pause = on_boss_pause
        self.on_boss_resume = on_boss_resume
        self.on_boss_victory = on_boss_victory
        self.on_boss_cancel = on_boss_cancel
        self.on_toggle_detection = on_toggle_detection

        self._accent_theme = None
        self._success_theme = None
        self._boss_theme = None
        self._boss_paused = False

    def create(self, parent: int):
        """Create the Play tab content."""
        self._accent_theme = create_accent_button_theme()
        self._success_theme = create_success_button_theme()
        self._boss_theme = create_boss_button_theme()

        with dpg.tab(label="Play", parent=parent):
            # Deaths row
            with dpg.group(horizontal=True):
                dpg.add_text("Deaths")
                dpg.add_text("0", tag="deaths_display", color=COLORS['red'])
                btn = dpg.add_button(label="+1", callback=self._on_death_click, width=40)
                dpg.bind_item_theme(btn, self._accent_theme)

            # Timer row
            with dpg.group(horizontal=True):
                dpg.add_text("Timer")
                dpg.add_text("00:00:00", tag="timer_display")
                btn_start = dpg.add_button(label="Start", tag="timer_start_btn", callback=self._on_timer_start, width=50)
                dpg.bind_item_theme(btn_start, self._success_theme)
                dpg.add_button(label="Stop", tag="timer_stop_btn", callback=self._on_timer_stop, width=50)
                dpg.add_button(label="Reset", callback=self._on_timer_reset, width=50)

            dpg.add_separator()

            # Boss mode row
            with dpg.group(horizontal=True):
                dpg.add_text("Boss")
                dpg.add_text("OFF", tag="boss_status", color=COLORS['text_dim'])
                dpg.add_text("Deaths:", color=COLORS['text_dim'])
                dpg.add_text("0", tag="boss_deaths_display", color=COLORS['purple'])

            # Boss buttons
            with dpg.group(horizontal=True, tag="boss_buttons_inactive"):
                btn_boss = dpg.add_button(label="Start Boss", callback=self._on_boss_start, width=100)
                dpg.bind_item_theme(btn_boss, self._boss_theme)

            with dpg.group(horizontal=True, tag="boss_buttons_active", show=False):
                btn_victory = dpg.add_button(label="Victory", callback=self._on_boss_victory_click, width=60)
                dpg.bind_item_theme(btn_victory, self._success_theme)
                dpg.add_button(label="Pause", tag="boss_pause_btn", callback=self._on_boss_pause, width=50)
                dpg.add_button(label="Cancel", callback=self._on_boss_cancel, width=55)

            dpg.add_separator()

            # Detection row
            with dpg.group(horizontal=True):
                dpg.add_text("Detection")
                dpg.add_text("ON", tag="detection_status", color=COLORS['green'])
                dpg.add_button(label="Toggle", callback=self._on_toggle_detection, width=60)

    def update(self, deaths: int, elapsed: int, is_running: bool,
               boss_mode: bool, boss_deaths: int, boss_paused: bool, detection_enabled: bool):
        """Update all displays."""
        if dpg.does_item_exist("deaths_display"):
            dpg.set_value("deaths_display", str(deaths))

        if dpg.does_item_exist("timer_display"):
            hours = elapsed // 3600000
            minutes = (elapsed % 3600000) // 60000
            seconds = (elapsed % 60000) // 1000
            dpg.set_value("timer_display", f"{hours:02d}:{minutes:02d}:{seconds:02d}")

        if dpg.does_item_exist("timer_start_btn"):
            dpg.configure_item("timer_start_btn", enabled=not is_running)
        if dpg.does_item_exist("timer_stop_btn"):
            dpg.configure_item("timer_stop_btn", enabled=is_running)

        if dpg.does_item_exist("boss_status"):
            if boss_mode:
                if boss_paused:
                    dpg.set_value("boss_status", "PAUSED")
                    dpg.configure_item("boss_status", color=COLORS['amber'])
                else:
                    dpg.set_value("boss_status", "ACTIVE")
                    dpg.configure_item("boss_status", color=COLORS['purple'])
            else:
                dpg.set_value("boss_status", "OFF")
                dpg.configure_item("boss_status", color=COLORS['text_dim'])

        # Update pause button label
        self._boss_paused = boss_paused
        if dpg.does_item_exist("boss_pause_btn"):
            dpg.set_item_label("boss_pause_btn", "Resume" if boss_paused else "Pause")

        if dpg.does_item_exist("boss_deaths_display"):
            dpg.set_value("boss_deaths_display", str(boss_deaths))

        if dpg.does_item_exist("boss_buttons_inactive"):
            dpg.configure_item("boss_buttons_inactive", show=not boss_mode)
        if dpg.does_item_exist("boss_buttons_active"):
            dpg.configure_item("boss_buttons_active", show=boss_mode)

        if dpg.does_item_exist("detection_status"):
            if detection_enabled:
                dpg.set_value("detection_status", "ON")
                dpg.configure_item("detection_status", color=COLORS['green'])
            else:
                dpg.set_value("detection_status", "OFF")
                dpg.configure_item("detection_status", color=COLORS['red'])

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
        """Show victory dialog."""
        vp_width = dpg.get_viewport_width()
        vp_height = dpg.get_viewport_height()

        with dpg.window(
            label="Victory",
            modal=True,
            width=250,
            height=100,
            pos=[(vp_width - 250) // 2, (vp_height - 100) // 2],
            tag="victory_dialog",
            no_resize=True
        ):
            dpg.add_input_text(tag="boss_name_input", width=-1, hint="Boss name")
            with dpg.group(horizontal=True):
                dpg.add_button(label="Cancel", callback=lambda: dpg.delete_item("victory_dialog"), width=80)
                btn = dpg.add_button(label="OK", callback=self._on_victory_confirm, width=80)
                dpg.bind_item_theme(btn, self._success_theme)

    def _on_victory_confirm(self):
        name = dpg.get_value("boss_name_input") if dpg.does_item_exist("boss_name_input") else ""
        if dpg.does_item_exist("victory_dialog"):
            dpg.delete_item("victory_dialog")
        self.on_boss_victory(name)

    def _on_boss_pause(self):
        if self._boss_paused:
            self.on_boss_resume()
        else:
            self.on_boss_pause()

    def _on_boss_cancel(self):
        self.on_boss_cancel()

    def _on_toggle_detection(self):
        self.on_toggle_detection()
