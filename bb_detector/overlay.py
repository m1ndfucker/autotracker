# bb_detector/overlay.py
import time
from typing import Dict, Optional
import dearpygui.dearpygui as dpg

from .config import Config


class Overlay:
    def __init__(self, config: Config):
        self.config = config
        self.visible = True
        self._initialized = False
        self._flash_reset_time: Optional[float] = None

        # State
        self.deaths = 0
        self.boss_mode = False
        self.boss_paused = False
        self.boss_deaths = 0
        self.connected = False
        self.detection_enabled = True

    def init(self):
        if self._initialized:
            return

        dpg.create_context()

        pos = self.config.get('overlay.position', [50, 50])
        opacity = self.config.get('overlay.opacity', 0.85)

        dpg.create_viewport(
            title='BB Detector',
            width=180,
            height=120,
            x_pos=pos[0],
            y_pos=pos[1],
            decorated=False,
            always_on_top=True,
            resizable=False,
        )

        # Theme
        with dpg.theme() as theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (11, 11, 12, int(255 * opacity)))
                dpg.add_theme_color(dpg.mvThemeCol_Text, (240, 236, 228))
                dpg.add_theme_color(dpg.mvThemeCol_Border, (60, 60, 60))

        # Main window
        with dpg.window(tag='main', no_title_bar=True, no_resize=True, no_move=False):
            # Status row
            with dpg.group(horizontal=True):
                dpg.add_text("*", tag='status_dot', color=(100, 100, 100))
                dpg.add_text("", tag='status_text', color=(150, 150, 150))

            dpg.add_separator()
            dpg.add_spacer(height=5)

            # Deaths count
            dpg.add_text("0", tag='deaths_count', color=(240, 236, 228))
            dpg.add_text("DEATHS", color=(100, 100, 100))

            dpg.add_spacer(height=5)

            # Boss section (hidden by default)
            with dpg.group(tag='boss_section', show=False):
                dpg.add_separator()
                with dpg.group(horizontal=True):
                    dpg.add_text("BOSS", color=(196, 48, 48))
                    dpg.add_text("0", tag='boss_deaths', color=(196, 48, 48))

            # Detection status
            dpg.add_spacer(height=5)
            dpg.add_text("detection: ON", tag='detection_status', color=(80, 80, 80))

        dpg.bind_theme(theme)
        dpg.setup_dearpygui()
        dpg.show_viewport()

        self._initialized = True

    def update(self, state: Dict):
        if not self._initialized:
            return

        self.deaths = state.get('deaths', 0)
        self.boss_mode = state.get('boss_mode', False)
        self.boss_paused = state.get('boss_paused', False)
        self.boss_deaths = state.get('boss_deaths', 0)
        self.connected = state.get('connected', False)
        self.detection_enabled = state.get('detection_enabled', True)

        # Update UI
        dpg.set_value('deaths_count', str(self.deaths))
        dpg.set_value('boss_deaths', str(self.boss_deaths))

        # Connection status
        if self.connected:
            dpg.configure_item('status_dot', color=(0, 200, 0))
            dpg.set_value('status_text', '')
        else:
            dpg.configure_item('status_dot', color=(200, 0, 0))
            dpg.set_value('status_text', 'OFFLINE')

        # Boss section
        dpg.configure_item('boss_section', show=self.boss_mode)

        # Detection status
        status = 'detection: ON' if self.detection_enabled else 'detection: OFF'
        dpg.set_value('detection_status', status)

    def flash_death(self):
        if self._initialized:
            dpg.configure_item('deaths_count', color=(255, 50, 50))
            self._flash_reset_time = time.time() + 0.3

    def render(self):
        if not self._initialized:
            return

        # Reset flash
        if self._flash_reset_time and time.time() > self._flash_reset_time:
            dpg.configure_item('deaths_count', color=(240, 236, 228))
            self._flash_reset_time = None

        dpg.render_dearpygui_frame()

    def toggle_visibility(self):
        self.visible = not self.visible
        if self._initialized:
            if self.visible:
                dpg.show_viewport()
            else:
                dpg.minimize_viewport()

    def save_position(self):
        if self._initialized:
            pos = dpg.get_viewport_pos()
            self.config.set('overlay.position', list(pos))

    def destroy(self):
        if self._initialized:
            self.save_position()
            dpg.destroy_context()
            self._initialized = False

    def is_running(self) -> bool:
        if not self._initialized:
            return False
        return dpg.is_dearpygui_running()
