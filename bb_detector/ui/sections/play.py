# bb_detector/ui/sections/play.py
"""Play section - main gameplay controls with card-based layout."""
import dearpygui.dearpygui as dpg
from typing import Callable
from ..theme import (
    COLORS,
    create_accent_button_theme,
    create_success_button_theme,
    create_boss_button_theme,
    create_section_card_theme,
)


class PlaySection:
    """Play section with deaths counter, timer, boss controls, and detection toggle."""

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
        self._card_theme = None
        self._boss_paused = False
        self._container_tag = "play_section_container"

    def create(self, parent: str):
        """Create the Play section content with card-based layout."""
        self._accent_theme = create_accent_button_theme()
        self._success_theme = create_success_button_theme()
        self._boss_theme = create_boss_button_theme()
        self._card_theme = create_section_card_theme()

        with dpg.child_window(
            parent=parent,
            tag=self._container_tag,
            border=False,
            autosize_x=True,
            autosize_y=True,
        ):
            # === Deaths Counter Card (prominent) ===
            with dpg.child_window(
                tag="play_deaths_card",
                height=90,
                border=True,
                autosize_x=True,
            ) as deaths_card:
                dpg.bind_item_theme(deaths_card, self._card_theme)

                # Centered deaths display
                with dpg.group(horizontal=False):
                    dpg.add_spacer(height=4)
                    dpg.add_text(
                        "DEATHS",
                        color=COLORS['text_tertiary'],
                    )
                    dpg.add_text(
                        "0",
                        tag="play_deaths_display",
                        color=COLORS['red'],
                    )
                    dpg.add_spacer(height=4)

                    # +1 Death button
                    btn = dpg.add_button(
                        label="+1 Death",
                        callback=self._on_death_click,
                        width=120,
                        height=28,
                    )
                    dpg.bind_item_theme(btn, self._accent_theme)

            dpg.add_spacer(height=8)

            # === Timer Card ===
            with dpg.child_window(
                tag="play_timer_card",
                height=70,
                border=True,
                autosize_x=True,
            ) as timer_card:
                dpg.bind_item_theme(timer_card, self._card_theme)

                with dpg.group(horizontal=True):
                    dpg.add_text("Timer", color=COLORS['text_tertiary'])
                    dpg.add_spacer(width=8)
                    dpg.add_text(
                        "00:00:00",
                        tag="play_timer_display",
                        color=COLORS['text_primary'],
                    )

                dpg.add_spacer(height=4)

                with dpg.group(horizontal=True):
                    btn_start = dpg.add_button(
                        label="Start",
                        tag="play_timer_start_btn",
                        callback=self._on_timer_start,
                        width=60,
                        height=26,
                    )
                    dpg.bind_item_theme(btn_start, self._success_theme)

                    dpg.add_button(
                        label="Stop",
                        tag="play_timer_stop_btn",
                        callback=self._on_timer_stop,
                        width=60,
                        height=26,
                    )

                    dpg.add_button(
                        label="Reset",
                        callback=self._on_timer_reset,
                        width=60,
                        height=26,
                    )

            dpg.add_spacer(height=8)

            # === Boss Mode Card ===
            with dpg.child_window(
                tag="play_boss_card",
                height=85,
                border=True,
                autosize_x=True,
            ) as boss_card:
                dpg.bind_item_theme(boss_card, self._card_theme)

                with dpg.group(horizontal=True):
                    dpg.add_text("Boss Mode", color=COLORS['text_tertiary'])
                    dpg.add_spacer(width=8)
                    dpg.add_text(
                        "OFF",
                        tag="play_boss_status",
                        color=COLORS['text_disabled'],
                    )
                    dpg.add_spacer(width=12)
                    dpg.add_text("Deaths:", color=COLORS['text_tertiary'])
                    dpg.add_text(
                        "0",
                        tag="play_boss_deaths_display",
                        color=COLORS['purple'],
                    )

                dpg.add_spacer(height=4)

                # Boss buttons (inactive state)
                with dpg.group(
                    horizontal=True,
                    tag="play_boss_buttons_inactive",
                ):
                    btn_boss = dpg.add_button(
                        label="Start Boss",
                        callback=self._on_boss_start,
                        width=100,
                        height=26,
                    )
                    dpg.bind_item_theme(btn_boss, self._boss_theme)

                # Boss buttons (active state)
                with dpg.group(
                    horizontal=True,
                    tag="play_boss_buttons_active",
                    show=False,
                ):
                    btn_victory = dpg.add_button(
                        label="Victory",
                        callback=self._on_boss_victory_click,
                        width=65,
                        height=26,
                    )
                    dpg.bind_item_theme(btn_victory, self._success_theme)

                    dpg.add_button(
                        label="Pause",
                        tag="play_boss_pause_btn",
                        callback=self._on_boss_pause,
                        width=55,
                        height=26,
                    )

                    dpg.add_button(
                        label="Cancel",
                        callback=self._on_boss_cancel,
                        width=55,
                        height=26,
                    )

            dpg.add_spacer(height=8)

            # === Detection Card ===
            with dpg.child_window(
                tag="play_detection_card",
                height=50,
                border=True,
                autosize_x=True,
            ) as detection_card:
                dpg.bind_item_theme(detection_card, self._card_theme)

                with dpg.group(horizontal=True):
                    dpg.add_text("Detection", color=COLORS['text_tertiary'])
                    dpg.add_spacer(width=8)
                    dpg.add_text(
                        "ON",
                        tag="play_detection_status",
                        color=COLORS['green'],
                    )
                    dpg.add_spacer(width=16)
                    dpg.add_button(
                        label="Toggle",
                        callback=self._on_toggle_detection,
                        width=70,
                        height=24,
                    )

    def update(
        self,
        deaths: int,
        elapsed: int,
        is_running: bool,
        boss_mode: bool,
        boss_deaths: int,
        boss_paused: bool,
        detection_enabled: bool,
    ):
        """Update all displays."""
        # Deaths counter
        if dpg.does_item_exist("play_deaths_display"):
            dpg.set_value("play_deaths_display", str(deaths))

        # Timer display
        if dpg.does_item_exist("play_timer_display"):
            hours = elapsed // 3600000
            minutes = (elapsed % 3600000) // 60000
            seconds = (elapsed % 60000) // 1000
            dpg.set_value("play_timer_display", f"{hours:02d}:{minutes:02d}:{seconds:02d}")

        # Timer buttons state
        if dpg.does_item_exist("play_timer_start_btn"):
            dpg.configure_item("play_timer_start_btn", enabled=not is_running)
        if dpg.does_item_exist("play_timer_stop_btn"):
            dpg.configure_item("play_timer_stop_btn", enabled=is_running)

        # Boss status
        if dpg.does_item_exist("play_boss_status"):
            if boss_mode:
                if boss_paused:
                    dpg.set_value("play_boss_status", "PAUSED")
                    dpg.configure_item("play_boss_status", color=COLORS['amber'])
                else:
                    dpg.set_value("play_boss_status", "ACTIVE")
                    dpg.configure_item("play_boss_status", color=COLORS['purple'])
            else:
                dpg.set_value("play_boss_status", "OFF")
                dpg.configure_item("play_boss_status", color=COLORS['text_disabled'])

        # Boss pause button label
        self._boss_paused = boss_paused
        if dpg.does_item_exist("play_boss_pause_btn"):
            dpg.set_item_label("play_boss_pause_btn", "Resume" if boss_paused else "Pause")

        # Boss deaths counter
        if dpg.does_item_exist("play_boss_deaths_display"):
            dpg.set_value("play_boss_deaths_display", str(boss_deaths))

        # Toggle boss button groups
        if dpg.does_item_exist("play_boss_buttons_inactive"):
            dpg.configure_item("play_boss_buttons_inactive", show=not boss_mode)
        if dpg.does_item_exist("play_boss_buttons_active"):
            dpg.configure_item("play_boss_buttons_active", show=boss_mode)

        # Detection status
        if dpg.does_item_exist("play_detection_status"):
            if detection_enabled:
                dpg.set_value("play_detection_status", "ON")
                dpg.configure_item("play_detection_status", color=COLORS['green'])
            else:
                dpg.set_value("play_detection_status", "OFF")
                dpg.configure_item("play_detection_status", color=COLORS['red'])

    def show(self):
        """Show the Play section."""
        if dpg.does_item_exist(self._container_tag):
            dpg.show_item(self._container_tag)

    def hide(self):
        """Hide the Play section."""
        if dpg.does_item_exist(self._container_tag):
            dpg.hide_item(self._container_tag)

    # === Internal callbacks ===

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
            tag="play_victory_dialog",
            no_resize=True,
        ):
            dpg.add_input_text(
                tag="play_boss_name_input",
                width=-1,
                hint="Boss name",
            )
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Cancel",
                    callback=lambda: dpg.delete_item("play_victory_dialog"),
                    width=80,
                )
                btn = dpg.add_button(
                    label="OK",
                    callback=self._on_victory_confirm,
                    width=80,
                )
                dpg.bind_item_theme(btn, self._success_theme)

    def _on_victory_confirm(self):
        name = ""
        if dpg.does_item_exist("play_boss_name_input"):
            name = dpg.get_value("play_boss_name_input")
        if dpg.does_item_exist("play_victory_dialog"):
            dpg.delete_item("play_victory_dialog")
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
