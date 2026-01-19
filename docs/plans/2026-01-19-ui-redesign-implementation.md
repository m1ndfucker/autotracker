# UI Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Redesign BB Death Detector UI with sidebar navigation, 3 sections (Play/Setup/History), and improved compact mode.

**Architecture:** Replace tab-based navigation with sidebar layout. Consolidate 5 tabs into 3 sections. Reorganize file structure from `ui/tabs/` to `ui/sections/` and `ui/dialogs/`. Update compact mode with boss controls and quick-add buttons.

**Tech Stack:** DearPyGui, Python 3.11+

---

## Task 1: Create Directory Structure

**Files:**
- Create: `bb_detector/ui/sections/__init__.py`
- Create: `bb_detector/ui/dialogs/__init__.py`

**Step 1: Create sections directory and init**

```python
# bb_detector/ui/sections/__init__.py
"""UI sections for sidebar navigation."""
from .play import PlaySection
from .setup import SetupSection
from .history import HistorySection

__all__ = ['PlaySection', 'SetupSection', 'HistorySection']
```

**Step 2: Create dialogs directory and init**

```python
# bb_detector/ui/dialogs/__init__.py
"""Modal dialogs."""
from .profile import ProfileDialog
from .milestone import MilestoneDialog
from .stats import StatsDialog

__all__ = ['ProfileDialog', 'MilestoneDialog', 'StatsDialog']
```

**Step 3: Commit**

```bash
git add bb_detector/ui/sections/ bb_detector/ui/dialogs/
git commit -m "chore: create ui/sections and ui/dialogs directories"
```

---

## Task 2: Update Theme with Card Styles

**Files:**
- Modify: `bb_detector/ui/theme.py`

**Step 1: Add card theme and sidebar styles to theme.py**

Add after `create_ghost_button_theme()` function:

```python
def create_sidebar_theme() -> int:
    """Sidebar navigation theme."""
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvChildWindow):
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, COLORS['bg_base'])
            dpg.add_theme_color(dpg.mvThemeCol_Border, (0, 0, 0, 0))
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 0, 0)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 0)
    return theme


def create_sidebar_item_theme(active: bool = False) -> int:
    """Sidebar item theme (active or inactive)."""
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvButton):
            if active:
                dpg.add_theme_color(dpg.mvThemeCol_Button, COLORS['bg_secondary'])
                dpg.add_theme_color(dpg.mvThemeCol_Text, COLORS['text_primary'])
            else:
                dpg.add_theme_color(dpg.mvThemeCol_Button, (0, 0, 0, 0))
                dpg.add_theme_color(dpg.mvThemeCol_Text, COLORS['text_tertiary'])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, COLORS['bg_elevated'])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, COLORS['bg_secondary'])
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 12, 8)
    return theme


def create_section_card_theme() -> int:
    """Card container for sections."""
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvChildWindow):
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, COLORS['bg_secondary'])
            dpg.add_theme_color(dpg.mvThemeCol_Border, COLORS['border_subtle'])
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 8)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 12, 12)
            dpg.add_theme_style(dpg.mvStyleVar_ChildBorderSize, 1)
    return theme


def create_deaths_display_theme() -> int:
    """Large deaths counter theme."""
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvText):
            dpg.add_theme_color(dpg.mvThemeCol_Text, COLORS['red'])
    return theme
```

**Step 2: Commit**

```bash
git add bb_detector/ui/theme.py
git commit -m "feat(theme): add sidebar and card themes"
```

---

## Task 3: Create Milestone Dialog

**Files:**
- Create: `bb_detector/ui/dialogs/milestone.py`

**Step 1: Create milestone dialog**

```python
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
```

**Step 2: Commit**

```bash
git add bb_detector/ui/dialogs/milestone.py
git commit -m "feat(dialogs): add MilestoneDialog"
```

---

## Task 4: Create Stats Dialog

**Files:**
- Create: `bb_detector/ui/dialogs/stats.py`

**Step 1: Create stats dialog**

```python
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
```

**Step 2: Commit**

```bash
git add bb_detector/ui/dialogs/stats.py
git commit -m "feat(dialogs): add StatsDialog"
```

---

## Task 5: Move Profile Dialog

**Files:**
- Move: `bb_detector/ui/profile_dialog.py` → `bb_detector/ui/dialogs/profile.py`

**Step 1: Move and update imports**

```bash
mv bb_detector/ui/profile_dialog.py bb_detector/ui/dialogs/profile.py
```

**Step 2: Update dialogs/__init__.py** (already has import)

**Step 3: Commit**

```bash
git add bb_detector/ui/dialogs/profile.py
git rm bb_detector/ui/profile_dialog.py
git commit -m "refactor: move profile_dialog to dialogs/profile"
```

---

## Task 6: Create Play Section

**Files:**
- Create: `bb_detector/ui/sections/play.py`

**Step 1: Create play section with card-based layout**

```python
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
    """Play section with deaths, timer, boss controls, and detection toggle."""

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

    def create(self, parent: str):
        """Create the Play section content."""
        self._accent_theme = create_accent_button_theme()
        self._success_theme = create_success_button_theme()
        self._boss_theme = create_boss_button_theme()
        self._card_theme = create_section_card_theme()

        with dpg.child_window(parent=parent, tag="play_section", border=False):
            # Deaths display - large centered
            dpg.add_spacer(height=20)
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=150)
                with dpg.group():
                    dpg.add_text("0", tag="play_deaths_display", color=COLORS['red'])
                    # Note: DearPyGui doesn't support font sizes per-item easily
                    # We'll use the default font but make it prominent
                    dpg.add_text("deaths", color=COLORS['text_tertiary'])

            dpg.add_spacer(height=10)

            # +1 Death button centered
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=160)
                btn = dpg.add_button(label="+1 Death", width=100, callback=self._on_death_click)
                dpg.bind_item_theme(btn, self._accent_theme)

            dpg.add_spacer(height=20)

            # Timer card
            with dpg.child_window(height=80, border=True, tag="timer_card"):
                dpg.bind_item_theme("timer_card", self._card_theme)
                dpg.add_spacer(height=8)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=10)
                    dpg.add_text("00:00:00", tag="play_timer_display")
                dpg.add_spacer(height=10)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=10)
                    btn_start = dpg.add_button(label="Start", tag="play_timer_start", width=80, callback=self._on_timer_start)
                    dpg.bind_item_theme(btn_start, self._success_theme)
                    dpg.add_button(label="Stop", tag="play_timer_stop", width=80, callback=self._on_timer_stop)
                    dpg.add_button(label="Reset", width=80, callback=self._on_timer_reset)

            dpg.add_spacer(height=10)

            # Boss card
            with dpg.child_window(height=90, border=True, tag="boss_card"):
                dpg.bind_item_theme("boss_card", self._card_theme)
                dpg.add_spacer(height=8)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=10)
                    dpg.add_text("Boss Mode", color=COLORS['text_tertiary'])
                    dpg.add_spacer(width=20)
                    dpg.add_text("OFF", tag="play_boss_status", color=COLORS['text_dim'])
                    dpg.add_spacer(width=20)
                    dpg.add_text("Deaths:", color=COLORS['text_tertiary'])
                    dpg.add_text("0", tag="play_boss_deaths", color=COLORS['purple'])

                dpg.add_spacer(height=10)

                # Boss buttons - inactive state
                with dpg.group(horizontal=True, tag="play_boss_inactive"):
                    dpg.add_spacer(width=10)
                    btn = dpg.add_button(label="Start Boss Fight", width=150, callback=self._on_boss_start)
                    dpg.bind_item_theme(btn, self._boss_theme)

                # Boss buttons - active state (hidden initially)
                with dpg.group(horizontal=True, tag="play_boss_active", show=False):
                    dpg.add_spacer(width=10)
                    btn_v = dpg.add_button(label="Victory", width=80, callback=self._on_boss_victory_click)
                    dpg.bind_item_theme(btn_v, self._success_theme)
                    dpg.add_button(label="Pause", tag="play_boss_pause", width=70, callback=self._on_boss_pause)
                    dpg.add_button(label="Cancel", width=70, callback=self._on_boss_cancel)

            dpg.add_spacer(height=10)

            # Detection card
            with dpg.child_window(height=50, border=True, tag="detection_card"):
                dpg.bind_item_theme("detection_card", self._card_theme)
                dpg.add_spacer(height=8)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=10)
                    dpg.add_text("Detection", color=COLORS['text_tertiary'])
                    dpg.add_spacer(width=20)
                    dpg.add_text("ON", tag="play_detection_status", color=COLORS['green'])
                    dpg.add_spacer(width=100)
                    dpg.add_button(label="Toggle", width=80, callback=self._on_toggle_detection)

    def update(self, deaths: int, elapsed: int, is_running: bool,
               boss_mode: bool, boss_deaths: int, boss_paused: bool, detection_enabled: bool):
        """Update all displays."""
        if dpg.does_item_exist("play_deaths_display"):
            dpg.set_value("play_deaths_display", str(deaths))

        if dpg.does_item_exist("play_timer_display"):
            hours = elapsed // 3600000
            minutes = (elapsed % 3600000) // 60000
            seconds = (elapsed % 60000) // 1000
            dpg.set_value("play_timer_display", f"{hours:02d}:{minutes:02d}:{seconds:02d}")

        if dpg.does_item_exist("play_timer_start"):
            dpg.configure_item("play_timer_start", enabled=not is_running)
        if dpg.does_item_exist("play_timer_stop"):
            dpg.configure_item("play_timer_stop", enabled=is_running)

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
                dpg.configure_item("play_boss_status", color=COLORS['text_dim'])

        self._boss_paused = boss_paused
        if dpg.does_item_exist("play_boss_pause"):
            dpg.set_item_label("play_boss_pause", "Resume" if boss_paused else "Pause")

        if dpg.does_item_exist("play_boss_deaths"):
            dpg.set_value("play_boss_deaths", str(boss_deaths))

        if dpg.does_item_exist("play_boss_inactive"):
            dpg.configure_item("play_boss_inactive", show=not boss_mode)
        if dpg.does_item_exist("play_boss_active"):
            dpg.configure_item("play_boss_active", show=boss_mode)

        # Detection status
        if dpg.does_item_exist("play_detection_status"):
            if detection_enabled:
                dpg.set_value("play_detection_status", "ON")
                dpg.configure_item("play_detection_status", color=COLORS['green'])
            else:
                dpg.set_value("play_detection_status", "OFF")
                dpg.configure_item("play_detection_status", color=COLORS['red'])

    def show(self):
        """Show this section."""
        if dpg.does_item_exist("play_section"):
            dpg.configure_item("play_section", show=True)

    def hide(self):
        """Hide this section."""
        if dpg.does_item_exist("play_section"):
            dpg.configure_item("play_section", show=False)

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
```

**Step 2: Commit**

```bash
git add bb_detector/ui/sections/play.py
git commit -m "feat(sections): add PlaySection with card layout"
```

---

## Task 7: Create Setup Section

**Files:**
- Create: `bb_detector/ui/sections/setup.py`

**Step 1: Create setup section (merged settings + calibration)**

```python
# bb_detector/ui/sections/setup.py
"""Setup section - detection region, settings, and hotkeys."""
import dearpygui.dearpygui as dpg
from typing import Callable, Dict, List, Optional, Any
import numpy as np
import cv2
import mss
from ..theme import COLORS, create_section_card_theme
from ..overlay_selector import show_overlay_selector
from ..corner_selector import CornerSelector


def _get_monitor_list() -> List[str]:
    """Get list of available monitors."""
    with mss.mss() as sct:
        count = len(sct.monitors) - 1
        return [f"Display {i+1}" for i in range(count)]


class SetupSection:
    """Setup section with region selection, detection settings, and hotkeys."""

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

        self._card_theme = None
        self._corner_selector: Optional[CornerSelector] = None
        self._preview_texture_id: Optional[int] = None
        self._preview_size = (200, 112)
        self._pending_progress: Optional[tuple[str, int]] = None
        self._pending_region: Optional[Dict] = None
        self._live_debug_active = False
        self._live_debug_counter = 0

    def create(self, parent: str):
        """Create the Setup section content."""
        self._card_theme = create_section_card_theme()

        with dpg.child_window(parent=parent, tag="setup_section", border=False, show=False):
            # Scrollable content
            with dpg.child_window(height=440, border=False):
                # Detection Region card
                dpg.add_text("DETECTION REGION", color=COLORS['text_tertiary'])
                dpg.add_spacer(height=5)

                with dpg.child_window(height=90, border=True, tag="region_card"):
                    dpg.bind_item_theme("region_card", self._card_theme)
                    dpg.add_spacer(height=5)
                    self._create_region_display()
                    dpg.add_spacer(height=8)
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Select Region", width=100, callback=self._on_select_region_visual)
                        dpg.add_button(label="F9 Mode", width=70, callback=self._on_select_region_f9)
                        dpg.add_button(label="Clear", width=60, callback=self._on_clear_region)

                dpg.add_text("", tag="setup_f9_instruction", color=COLORS['accent'], wrap=400)
                dpg.add_spacer(height=10)

                # Test & Preview card
                dpg.add_text("TEST & PREVIEW", color=COLORS['text_tertiary'])
                dpg.add_spacer(height=5)

                with dpg.child_window(height=160, border=True, tag="preview_card"):
                    dpg.bind_item_theme("preview_card", self._card_theme)
                    dpg.add_spacer(height=5)

                    with dpg.group(horizontal=True):
                        # Preview image
                        self._create_preview_texture()
                        with dpg.drawlist(tag="setup_preview_drawlist", width=200, height=112):
                            dpg.draw_image(self._preview_texture_id, pmin=(0, 0), pmax=(200, 112), tag="setup_preview_image")

                        dpg.add_spacer(width=15)

                        with dpg.group():
                            dpg.add_text("Result:", color=COLORS['text_tertiary'])
                            dpg.add_text("-", tag="setup_detection_result", color=COLORS['text_dim'])

                    dpg.add_spacer(height=8)
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Capture & Test", width=110, callback=self._on_capture_and_test)
                        dpg.add_button(label="Live Preview", width=100, tag="setup_live_btn", callback=self._on_toggle_live)

                dpg.add_spacer(height=10)

                # Detection Settings card
                dpg.add_text("DETECTION SETTINGS", color=COLORS['text_tertiary'])
                dpg.add_spacer(height=5)

                with dpg.child_window(height=100, border=True, tag="settings_card"):
                    dpg.bind_item_theme("settings_card", self._card_theme)
                    dpg.add_spacer(height=5)

                    monitors = _get_monitor_list()
                    with dpg.group(horizontal=True):
                        dpg.add_text("Monitor", color=COLORS['text_tertiary'], indent=5)
                        dpg.add_combo(
                            items=monitors if monitors else ["Display 1"],
                            default_value=monitors[0] if monitors else "Display 1",
                            tag="setup_monitor",
                            width=150,
                            callback=self._on_setting_change
                        )

                    with dpg.group(horizontal=True):
                        dpg.add_text("Game", color=COLORS['text_tertiary'], indent=5)
                        dpg.add_combo(
                            items=["Bloodborne", "Dark Souls 3", "Dark Souls Remastered", "Elden Ring", "Sekiro", "Custom"],
                            default_value="Bloodborne",
                            tag="setup_game",
                            width=150,
                            callback=self._on_setting_change
                        )

                    with dpg.group(horizontal=True):
                        dpg.add_text("Cooldown", color=COLORS['text_tertiary'], indent=5)
                        dpg.add_combo(
                            items=["3 sec", "5 sec", "10 sec"],
                            default_value="5 sec",
                            tag="setup_cooldown",
                            width=150,
                            callback=self._on_setting_change
                        )

                dpg.add_spacer(height=10)

                # Hotkeys card
                dpg.add_text("HOTKEYS", color=COLORS['text_tertiary'])
                dpg.add_spacer(height=5)

                with dpg.child_window(height=110, border=True, tag="hotkeys_card"):
                    dpg.bind_item_theme("hotkeys_card", self._card_theme)
                    dpg.add_spacer(height=5)

                    hotkeys = [
                        ("Manual Death", "Ctrl+Shift+D"),
                        ("Toggle Boss", "Ctrl+Shift+B"),
                        ("Toggle Mode", "Ctrl+Shift+O"),
                        ("Pause Detect", "Ctrl+Shift+P"),
                    ]

                    for label, default in hotkeys:
                        with dpg.group(horizontal=True):
                            dpg.add_text(label, color=COLORS['text_tertiary'], indent=5)
                            dpg.add_spacer(width=20)
                            dpg.add_button(label=default, width=140)

    def _create_region_display(self):
        """Create region info display."""
        window_name = self.config.get('detection.region.window_name', '')

        if window_name:
            w_pct = self.config.get('detection.region.w_percent', 0)
            h_pct = self.config.get('detection.region.h_percent', 0)
            x_pct = self.config.get('detection.region.x_percent', 0)
            y_pct = self.config.get('detection.region.y_percent', 0)

            if w_pct > 0 and h_pct > 0:
                text = f"Window: {window_name}\nRegion: {x_pct*100:.0f}%,{y_pct*100:.0f}% - {w_pct*100:.0f}%x{h_pct*100:.0f}%"
            else:
                text = f"Window: {window_name} (no region)"
        else:
            region_w = self.config.get('detection.region.width', 0)
            region_h = self.config.get('detection.region.height', 0)

            if region_w > 0 and region_h > 0:
                region_x = self.config.get('detection.region.x', 0)
                region_y = self.config.get('detection.region.y', 0)
                text = f"Absolute: {region_x},{region_y} - {region_w}x{region_h}"
            else:
                text = "Full screen (no region set)"

        dpg.add_text(text, tag="setup_region_display", color=COLORS['text_secondary'], wrap=380)

    def _update_region_display(self):
        """Update region display text."""
        window_name = self.config.get('detection.region.window_name', '')

        if window_name:
            w_pct = self.config.get('detection.region.w_percent', 0)
            h_pct = self.config.get('detection.region.h_percent', 0)
            x_pct = self.config.get('detection.region.x_percent', 0)
            y_pct = self.config.get('detection.region.y_percent', 0)

            if w_pct > 0 and h_pct > 0:
                text = f"Window: {window_name}\nRegion: {x_pct*100:.0f}%,{y_pct*100:.0f}% - {w_pct*100:.0f}%x{h_pct*100:.0f}%"
            else:
                text = f"Window: {window_name} (no region)"
        else:
            region_w = self.config.get('detection.region.width', 0)
            if region_w > 0:
                region_x = self.config.get('detection.region.x', 0)
                region_y = self.config.get('detection.region.y', 0)
                region_h = self.config.get('detection.region.height', 0)
                text = f"Absolute: {region_x},{region_y} - {region_w}x{region_h}"
            else:
                text = "Full screen (no region set)"

        if dpg.does_item_exist("setup_region_display"):
            dpg.set_value("setup_region_display", text)

    def _create_preview_texture(self):
        """Create placeholder texture for preview."""
        w, h = self._preview_size
        placeholder = np.full((h, w, 4), 40, dtype=np.float32) / 255.0

        with dpg.texture_registry():
            self._preview_texture_id = dpg.add_dynamic_texture(
                width=w,
                height=h,
                default_value=placeholder.flatten().tolist(),
                tag="setup_preview_texture"
            )

    def _update_preview(self, frame: np.ndarray):
        """Update preview texture."""
        if frame is None or not dpg.does_item_exist("setup_preview_texture"):
            return

        w, h = self._preview_size
        frame_resized = cv2.resize(frame, (w, h))

        if len(frame_resized.shape) == 2:
            frame_rgba = cv2.cvtColor(frame_resized, cv2.COLOR_GRAY2RGBA)
        elif frame_resized.shape[2] == 3:
            frame_rgba = cv2.cvtColor(frame_resized, cv2.COLOR_RGB2RGBA)
        else:
            frame_rgba = frame_resized

        frame_flat = frame_rgba.flatten().astype(np.float32) / 255.0
        dpg.set_value("setup_preview_texture", frame_flat.tolist())

    def _get_region_for_capture(self) -> Dict:
        """Get region dict for capture."""
        window_name = self.config.get('detection.region.window_name', '')

        if window_name:
            return {
                'window_name': window_name,
                'x_percent': self.config.get('detection.region.x_percent', 0),
                'y_percent': self.config.get('detection.region.y_percent', 0),
                'w_percent': self.config.get('detection.region.w_percent', 0),
                'h_percent': self.config.get('detection.region.h_percent', 0),
            }
        return {
            'x': self.config.get('detection.region.x', 0),
            'y': self.config.get('detection.region.y', 0),
            'width': self.config.get('detection.region.width', 0),
            'height': self.config.get('detection.region.height', 0),
        }

    def show(self):
        if dpg.does_item_exist("setup_section"):
            dpg.configure_item("setup_section", show=True)

    def hide(self):
        if dpg.does_item_exist("setup_section"):
            dpg.configure_item("setup_section", show=False)

    def update(self):
        """Process pending updates."""
        if self._pending_progress is not None:
            message, step = self._pending_progress
            self._pending_progress = None
            if dpg.does_item_exist("setup_f9_instruction"):
                dpg.set_value("setup_f9_instruction", "" if step in (-1, 2) else message)

        if self._pending_region is not None:
            region = self._pending_region
            self._pending_region = None
            self.on_save_region(region)
            self._update_region_display()
            if dpg.does_item_exist("setup_f9_instruction"):
                dpg.set_value("setup_f9_instruction", "")
            self._on_capture_and_test()

        if self._live_debug_active:
            self._live_debug_counter += 1
            if self._live_debug_counter >= 10:
                self._live_debug_counter = 0
                self._update_live_debug()

    def on_f9_pressed(self):
        if self._corner_selector and self._corner_selector.is_active:
            self._corner_selector.on_f9_pressed()

    def _on_select_region_visual(self):
        if dpg.does_item_exist("setup_f9_instruction"):
            dpg.set_value("setup_f9_instruction", "Opening visual selector...")
        show_overlay_selector(
            on_complete=self._on_region_selected,
            on_cancel=self._on_region_cancel,
            run_in_thread=True
        )

    def _on_select_region_f9(self):
        if dpg.does_item_exist("setup_f9_instruction"):
            dpg.set_value("setup_f9_instruction", "Move cursor to TOP-LEFT corner and press F9...")
        self._corner_selector = CornerSelector(
            on_complete=self._on_region_selected,
            on_cancel=self._on_region_cancel,
            on_progress=self._on_region_progress
        )
        self._corner_selector.start()

    def _on_region_selected(self, region: dict):
        self._pending_region = region

    def _on_region_cancel(self):
        self._pending_progress = ("", -1)

    def _on_region_progress(self, message: str, step: int):
        self._pending_progress = (message, step)

    def _on_clear_region(self):
        self.on_save_region({'x': 0, 'y': 0, 'width': 0, 'height': 0})
        self._update_region_display()

    def _on_capture_and_test(self):
        region = self._get_region_for_capture()
        frame = self.on_capture_region(region)

        if frame is None:
            if dpg.does_item_exist("setup_detection_result"):
                dpg.set_value("setup_detection_result", "Capture failed")
                dpg.configure_item("setup_detection_result", color=COLORS['red'])
            return

        self._update_preview(frame)
        is_match, confidence = self.on_test_detection(frame)

        if dpg.does_item_exist("setup_detection_result"):
            if is_match:
                dpg.set_value("setup_detection_result", f"MATCH ({confidence:.2f})")
                dpg.configure_item("setup_detection_result", color=COLORS['green'])
            else:
                dpg.set_value("setup_detection_result", f"No match ({confidence:.2f})")
                dpg.configure_item("setup_detection_result", color=COLORS['red'])

    def _on_toggle_live(self):
        self._live_debug_active = not self._live_debug_active
        if dpg.does_item_exist("setup_live_btn"):
            dpg.set_item_label("setup_live_btn", "Stop" if self._live_debug_active else "Live Preview")

    def _update_live_debug(self):
        try:
            region = self._get_region_for_capture()
            frame = self.on_capture_region(region)
            if frame is None:
                return
            self._update_preview(frame)
            is_match, _ = self.on_test_detection(frame)
            if dpg.does_item_exist("setup_detection_result"):
                if is_match:
                    dpg.set_value("setup_detection_result", "MATCH!")
                    dpg.configure_item("setup_detection_result", color=COLORS['green'])
                else:
                    dpg.set_value("setup_detection_result", "No match")
                    dpg.configure_item("setup_detection_result", color=COLORS['text_secondary'])
        except Exception:
            pass

    def _on_setting_change(self, sender, app_data):
        settings = {}
        if dpg.does_item_exist("setup_monitor"):
            val = dpg.get_value("setup_monitor")
            settings['detection.monitor'] = int(val.split()[-1]) - 1
        if dpg.does_item_exist("setup_game"):
            settings['current_game'] = dpg.get_value("setup_game")
        if dpg.does_item_exist("setup_cooldown"):
            val = dpg.get_value("setup_cooldown")
            settings['detection.death_cooldown'] = float(val.split()[0])
        self.on_save_settings(settings)
```

**Step 2: Commit**

```bash
git add bb_detector/ui/sections/setup.py
git commit -m "feat(sections): add SetupSection (merged settings + calibration)"
```

---

## Task 8: Create History Section

**Files:**
- Create: `bb_detector/ui/sections/history.py`

**Step 1: Create history section (merged history + stats)**

```python
# bb_detector/ui/sections/history.py
"""History section - session stats, milestones, character stats, boss fights, deaths."""
import dearpygui.dearpygui as dpg
from typing import Callable, List
from ..theme import COLORS, create_section_card_theme, create_accent_button_theme
from ..dialogs.milestone import MilestoneDialog
from ..dialogs.stats import StatsDialog
from ...state import Milestone, DeathTimestamp, BossFight, CharacterStats


def format_time(ms: int) -> str:
    """Format milliseconds as HH:MM:SS or MM:SS."""
    total_seconds = ms // 1000
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


class HistorySection:
    """History section with milestones, stats, boss fights, and deaths."""

    def __init__(
        self,
        on_add_milestone: Callable[[str, str], None],
        on_delete_milestone: Callable[[str], None],
        on_add_stats: Callable[[dict], None],
        on_delete_stats: Callable[[str], None],
    ):
        self.on_add_milestone = on_add_milestone
        self.on_delete_milestone = on_delete_milestone
        self.on_add_stats = on_add_stats
        self.on_delete_stats = on_delete_stats

        self._milestones: List[Milestone] = []
        self._death_timestamps: List[DeathTimestamp] = []
        self._boss_fights: List[BossFight] = []
        self._character_stats: List[CharacterStats] = []
        self._deaths = 0
        self._elapsed = 0

        self._card_theme = None
        self._accent_theme = None

    def create(self, parent: str):
        """Create the History section content."""
        self._card_theme = create_section_card_theme()
        self._accent_theme = create_accent_button_theme()

        with dpg.child_window(parent=parent, tag="history_section", border=False, show=False):
            # Scrollable content
            with dpg.child_window(height=440, border=False):
                # Current Session card
                dpg.add_text("CURRENT SESSION", color=COLORS['text_tertiary'])
                dpg.add_spacer(height=5)

                with dpg.child_window(height=60, border=True, tag="session_card"):
                    dpg.bind_item_theme("session_card", self._card_theme)
                    dpg.add_spacer(height=5)
                    with dpg.group(horizontal=True):
                        dpg.add_text("Deaths:", color=COLORS['text_tertiary'], indent=5)
                        dpg.add_text("0", tag="hist_deaths", color=COLORS['red'])
                        dpg.add_spacer(width=30)
                        dpg.add_text("Time:", color=COLORS['text_tertiary'])
                        dpg.add_text("00:00:00", tag="hist_time")
                    with dpg.group(horizontal=True):
                        dpg.add_text("Bosses:", color=COLORS['text_tertiary'], indent=5)
                        dpg.add_text("0", tag="hist_bosses", color=COLORS['teal'])
                        dpg.add_spacer(width=30)
                        dpg.add_text("Milestones:", color=COLORS['text_tertiary'])
                        dpg.add_text("0", tag="hist_milestones", color=COLORS['purple'])

                dpg.add_spacer(height=10)

                # Milestones section
                with dpg.group(horizontal=True):
                    dpg.add_text("MILESTONES", color=COLORS['text_tertiary'])
                    dpg.add_spacer(width=250)
                    btn = dpg.add_button(label="+ Add", width=60, callback=self._show_milestone_dialog)
                    dpg.bind_item_theme(btn, self._accent_theme)

                dpg.add_spacer(height=5)

                with dpg.child_window(height=100, border=True, tag="milestones_card"):
                    dpg.bind_item_theme("milestones_card", self._card_theme)
                    dpg.add_text("No milestones yet", tag="hist_no_milestones", color=COLORS['text_dim'])

                dpg.add_spacer(height=10)

                # Character Stats section
                with dpg.group(horizontal=True):
                    dpg.add_text("CHARACTER STATS", color=COLORS['text_tertiary'])
                    dpg.add_spacer(width=230)
                    btn = dpg.add_button(label="+ Add", width=60, callback=self._show_stats_dialog)
                    dpg.bind_item_theme(btn, self._accent_theme)

                dpg.add_spacer(height=5)

                with dpg.child_window(height=70, border=True, tag="stats_card"):
                    dpg.bind_item_theme("stats_card", self._card_theme)
                    dpg.add_text("No stats recorded", tag="hist_no_stats", color=COLORS['text_dim'])

                dpg.add_spacer(height=10)
                dpg.add_separator()
                dpg.add_spacer(height=10)

                # Boss Fights section
                dpg.add_text("BOSS FIGHTS", color=COLORS['text_tertiary'])
                dpg.add_spacer(height=5)

                with dpg.child_window(height=80, border=True, tag="bosses_card"):
                    dpg.bind_item_theme("bosses_card", self._card_theme)
                    dpg.add_text("No boss fights yet", tag="hist_no_bosses", color=COLORS['text_dim'])

                dpg.add_spacer(height=10)

                # Recent Deaths section
                dpg.add_text("RECENT DEATHS", color=COLORS['text_tertiary'])
                dpg.add_spacer(height=5)

                with dpg.child_window(height=70, border=True, tag="deaths_card"):
                    dpg.bind_item_theme("deaths_card", self._card_theme)
                    dpg.add_text("No deaths recorded", tag="hist_no_deaths", color=COLORS['text_dim'])

    def update(
        self,
        deaths: int,
        elapsed: int,
        milestones: List[Milestone],
        death_timestamps: List[DeathTimestamp],
        boss_fights: List[BossFight],
        character_stats: List[CharacterStats],
    ):
        """Update all data."""
        self._deaths = deaths
        self._elapsed = elapsed
        self._milestones = milestones
        self._death_timestamps = death_timestamps
        self._boss_fights = boss_fights
        self._character_stats = character_stats

        self._update_session_summary()
        self._update_milestones()
        self._update_stats()
        self._update_bosses()
        self._update_deaths()

    def _update_session_summary(self):
        """Update session summary card."""
        if dpg.does_item_exist("hist_deaths"):
            dpg.set_value("hist_deaths", str(self._deaths))
        if dpg.does_item_exist("hist_time"):
            dpg.set_value("hist_time", format_time(self._elapsed))
        if dpg.does_item_exist("hist_bosses"):
            dpg.set_value("hist_bosses", str(len(self._boss_fights)))
        if dpg.does_item_exist("hist_milestones"):
            dpg.set_value("hist_milestones", str(len(self._milestones)))

    def _update_milestones(self):
        """Update milestones list."""
        if not dpg.does_item_exist("milestones_card"):
            return

        children = dpg.get_item_children("milestones_card", 1)
        if children:
            for child in children:
                dpg.delete_item(child)

        if not self._milestones:
            dpg.add_text("No milestones yet", parent="milestones_card", color=COLORS['text_dim'])
            return

        for milestone in reversed(self._milestones[-5:]):
            with dpg.group(horizontal=True, parent="milestones_card"):
                dpg.add_text(milestone.icon, color=COLORS['purple'])
                dpg.add_text(milestone.name, color=COLORS['text_primary'])
                dpg.add_text(f"@ {format_time(milestone.timestamp)}", color=COLORS['text_dim'])
                dpg.add_button(label="x", width=20, user_data=milestone.id, callback=self._on_delete_milestone)

    def _update_stats(self):
        """Update character stats list."""
        if not dpg.does_item_exist("stats_card"):
            return

        children = dpg.get_item_children("stats_card", 1)
        if children:
            for child in children:
                dpg.delete_item(child)

        if not self._character_stats:
            dpg.add_text("No stats recorded", parent="stats_card", color=COLORS['text_dim'])
            return

        for stat in reversed(self._character_stats[-3:]):
            with dpg.group(horizontal=True, parent="stats_card"):
                dpg.add_text(f"Lv{stat.level}", color=COLORS['text_primary'])
                dpg.add_text(f"VIT:{stat.vitality} END:{stat.endurance} STR:{stat.strength}", color=COLORS['text_secondary'])
                dpg.add_button(label="x", width=20, user_data=stat.id, callback=self._on_delete_stats)

    def _update_bosses(self):
        """Update boss fights list."""
        if not dpg.does_item_exist("bosses_card"):
            return

        children = dpg.get_item_children("bosses_card", 1)
        if children:
            for child in children:
                dpg.delete_item(child)

        if not self._boss_fights:
            dpg.add_text("No boss fights yet", parent="bosses_card", color=COLORS['text_dim'])
            return

        for boss in reversed(self._boss_fights[-4:]):
            with dpg.group(horizontal=True, parent="bosses_card"):
                dpg.add_text(boss.name or "Unknown", color=COLORS['teal'])
                dpg.add_text(f"{boss.deaths_on_boss} deaths", color=COLORS['red'])
                dpg.add_text(f"({format_time(boss.duration)})", color=COLORS['text_dim'])

    def _update_deaths(self):
        """Update deaths list."""
        if not dpg.does_item_exist("deaths_card"):
            return

        children = dpg.get_item_children("deaths_card", 1)
        if children:
            for child in children:
                dpg.delete_item(child)

        if not self._death_timestamps:
            dpg.add_text("No deaths recorded", parent="deaths_card", color=COLORS['text_dim'])
            return

        for death in reversed(self._death_timestamps[-5:]):
            with dpg.group(horizontal=True, parent="deaths_card"):
                dpg.add_text(f"#{death.death_number}", color=COLORS['red'])
                dpg.add_text(f"@ {format_time(death.timestamp)}", color=COLORS['text_dim'])

    def show(self):
        if dpg.does_item_exist("history_section"):
            dpg.configure_item("history_section", show=True)

    def hide(self):
        if dpg.does_item_exist("history_section"):
            dpg.configure_item("history_section", show=False)

    def _show_milestone_dialog(self):
        dialog = MilestoneDialog(on_add=self.on_add_milestone)
        dialog.show()

    def _show_stats_dialog(self):
        dialog = StatsDialog(on_add=self.on_add_stats)
        dialog.show()

    def _on_delete_milestone(self, sender, app_data, user_data):
        if user_data:
            self.on_delete_milestone(user_data)

    def _on_delete_stats(self, sender, app_data, user_data):
        if user_data:
            self.on_delete_stats(user_data)
```

**Step 2: Commit**

```bash
git add bb_detector/ui/sections/history.py
git commit -m "feat(sections): add HistorySection (merged history + stats)"
```

---

## Task 9: Update Compact Mode

**Files:**
- Modify: `bb_detector/ui/compact.py`

**Step 1: Rewrite compact.py with new layout**

```python
# bb_detector/ui/compact.py
"""Compact mode window - minimal UI for gameplay."""
import dearpygui.dearpygui as dpg
from typing import Callable
from .theme import COLORS, create_accent_button_theme, create_success_button_theme, create_boss_button_theme, create_ghost_button_theme
from .dialogs.milestone import MilestoneDialog
from .dialogs.stats import StatsDialog


class CompactWindow:
    """Compact floating window for gameplay."""

    WIDTH = 280
    HEIGHT = 160

    def __init__(
        self,
        on_expand: Callable[[], None],
        on_boss_start: Callable[[], None] = None,
        on_boss_pause: Callable[[], None] = None,
        on_boss_resume: Callable[[], None] = None,
        on_boss_victory: Callable[[str], None] = None,
        on_boss_cancel: Callable[[], None] = None,
        on_add_milestone: Callable[[str, str], None] = None,
        on_add_stats: Callable[[dict], None] = None,
    ):
        self.on_expand = on_expand
        self.on_boss_start = on_boss_start or (lambda: None)
        self.on_boss_pause = on_boss_pause or (lambda: None)
        self.on_boss_resume = on_boss_resume or (lambda: None)
        self.on_boss_victory = on_boss_victory or (lambda n: None)
        self.on_boss_cancel = on_boss_cancel or (lambda: None)
        self.on_add_milestone = on_add_milestone or (lambda n, i: None)
        self.on_add_stats = on_add_stats or (lambda s: None)

        self._accent_theme = None
        self._success_theme = None
        self._boss_theme = None
        self._ghost_theme = None
        self._boss_paused = False
        self._boss_mode = False

    def create(self):
        """Create the compact window (hidden initially)."""
        self._accent_theme = create_accent_button_theme()
        self._success_theme = create_success_button_theme()
        self._boss_theme = create_boss_button_theme()
        self._ghost_theme = create_ghost_button_theme()

        with dpg.window(
            tag="compact_window",
            label="",
            no_title_bar=True,
            no_resize=True,
            width=self.WIDTH,
            height=self.HEIGHT,
            show=False,
            no_background=False,
        ):
            # Header: Deaths, Timer, Expand button
            with dpg.group(horizontal=True):
                dpg.add_text("0", tag="compact_deaths", color=COLORS['red'])
                dpg.add_spacer(width=60)
                dpg.add_text("00:00:00", tag="compact_timer")
                dpg.add_spacer(width=60)
                btn = dpg.add_button(label="[+]", width=30, callback=self._on_expand)
                dpg.bind_item_theme(btn, self._ghost_theme)

            dpg.add_separator()

            # Boss section - inactive
            with dpg.group(tag="compact_boss_inactive"):
                with dpg.group(horizontal=True):
                    dpg.add_text("Boss Mode: OFF", color=COLORS['text_dim'])
                    dpg.add_spacer(width=50)
                    btn = dpg.add_button(label="Start Boss", width=100, callback=self._on_boss_start)
                    dpg.bind_item_theme(btn, self._boss_theme)

            # Boss section - active
            with dpg.group(tag="compact_boss_active", show=False):
                with dpg.group(horizontal=True):
                    dpg.add_text("BOSS ACTIVE", tag="compact_boss_status", color=COLORS['purple'])
                    dpg.add_spacer(width=30)
                    dpg.add_text("Deaths:", color=COLORS['text_tertiary'])
                    dpg.add_text("0", tag="compact_boss_deaths", color=COLORS['purple'])

                with dpg.group(horizontal=True):
                    btn_v = dpg.add_button(label="Victory", width=70, callback=self._on_boss_victory)
                    dpg.bind_item_theme(btn_v, self._success_theme)
                    dpg.add_button(label="Pause", tag="compact_boss_pause", width=60, callback=self._on_boss_pause)
                    dpg.add_button(label="Cancel", width=60, callback=self._on_boss_cancel)

            dpg.add_separator()

            # Quick add buttons
            with dpg.group(horizontal=True):
                btn_m = dpg.add_button(label="+ Milestone", width=100, callback=self._show_milestone_dialog)
                dpg.bind_item_theme(btn_m, self._ghost_theme)
                dpg.add_spacer(width=30)
                btn_s = dpg.add_button(label="+ Stats", width=80, callback=self._show_stats_dialog)
                dpg.bind_item_theme(btn_s, self._ghost_theme)

            # Status bar
            with dpg.group(horizontal=True):
                dpg.add_text("●", tag="compact_status_dot", color=COLORS['red'])
                dpg.add_text("Offline", tag="compact_status", color=COLORS['text_dim'])
                dpg.add_spacer(width=100)
                dpg.add_text("", tag="compact_profile", color=COLORS['text_tertiary'])

    def update(self, deaths: int, elapsed: int, boss_mode: bool, boss_deaths: int,
               boss_paused: bool, connected: bool, profile: str):
        """Update compact window displays."""
        if dpg.does_item_exist("compact_deaths"):
            dpg.set_value("compact_deaths", str(deaths))

        if dpg.does_item_exist("compact_timer"):
            hours = elapsed // 3600000
            minutes = (elapsed % 3600000) // 60000
            seconds = (elapsed % 60000) // 1000
            dpg.set_value("compact_timer", f"{hours:02d}:{minutes:02d}:{seconds:02d}")

        self._boss_mode = boss_mode
        self._boss_paused = boss_paused

        if dpg.does_item_exist("compact_boss_inactive"):
            dpg.configure_item("compact_boss_inactive", show=not boss_mode)
        if dpg.does_item_exist("compact_boss_active"):
            dpg.configure_item("compact_boss_active", show=boss_mode)

        if dpg.does_item_exist("compact_boss_status"):
            if boss_paused:
                dpg.set_value("compact_boss_status", "PAUSED")
                dpg.configure_item("compact_boss_status", color=COLORS['amber'])
            else:
                dpg.set_value("compact_boss_status", "BOSS ACTIVE")
                dpg.configure_item("compact_boss_status", color=COLORS['purple'])

        if dpg.does_item_exist("compact_boss_pause"):
            dpg.set_item_label("compact_boss_pause", "Resume" if boss_paused else "Pause")

        if dpg.does_item_exist("compact_boss_deaths"):
            dpg.set_value("compact_boss_deaths", str(boss_deaths))

        if dpg.does_item_exist("compact_status_dot"):
            dpg.configure_item("compact_status_dot", color=COLORS['green'] if connected else COLORS['red'])
        if dpg.does_item_exist("compact_status"):
            dpg.set_value("compact_status", "Online" if connected else "Offline")
        if dpg.does_item_exist("compact_profile"):
            dpg.set_value("compact_profile", profile)

    def show(self):
        if dpg.does_item_exist("compact_window"):
            dpg.configure_item("compact_window", show=True)
            dpg.set_viewport_width(self.WIDTH + 20)
            dpg.set_viewport_height(self.HEIGHT + 20)

    def hide(self):
        if dpg.does_item_exist("compact_window"):
            dpg.configure_item("compact_window", show=False)

    def _on_expand(self):
        self.on_expand()

    def _on_boss_start(self):
        self.on_boss_start()

    def _on_boss_pause(self):
        if self._boss_paused:
            self.on_boss_resume()
        else:
            self.on_boss_pause()

    def _on_boss_victory(self):
        # Simple victory without dialog in compact mode
        self.on_boss_victory("")

    def _on_boss_cancel(self):
        self.on_boss_cancel()

    def _show_milestone_dialog(self):
        dialog = MilestoneDialog(on_add=self.on_add_milestone)
        dialog.show()

    def _show_stats_dialog(self):
        dialog = StatsDialog(on_add=self.on_add_stats)
        dialog.show()
```

**Step 2: Commit**

```bash
git add bb_detector/ui/compact.py
git commit -m "feat(compact): rewrite with boss controls and quick-add buttons"
```

---

## Task 10: Update Main App with Sidebar Layout

**Files:**
- Modify: `bb_detector/ui/app.py`

**Step 1: Rewrite app.py with sidebar navigation**

```python
# bb_detector/ui/app.py
"""Main application window with sidebar navigation."""
import dearpygui.dearpygui as dpg
from typing import Optional, Callable
from pathlib import Path
import sys

from .theme import create_theme, create_sidebar_theme, create_sidebar_item_theme, COLORS
from .sections.play import PlaySection
from .sections.setup import SetupSection
from .sections.history import HistorySection
from .compact import CompactWindow
from .dialogs.profile import ProfileDialog
from ..state import StateManager
from ..config import Config


class App:
    """Main application window manager with sidebar navigation."""

    WIDTH = 600
    HEIGHT = 500
    SIDEBAR_WIDTH = 150

    def __init__(
        self,
        config: Config,
        state: StateManager,
        on_manual_death: Callable,
        on_timer_start: Callable,
        on_timer_stop: Callable,
        on_timer_reset: Callable,
        on_boss_start: Callable,
        on_boss_pause: Callable,
        on_boss_resume: Callable,
        on_boss_victory: Callable,
        on_boss_cancel: Callable,
        on_toggle_detection: Callable,
        on_profile_select: Callable,
        on_capture: Callable,
        on_capture_region: Callable,
        on_test_detection: Callable,
        on_save_region: Callable,
        on_quit: Callable,
        on_f9_pressed: Callable = None,
        on_add_milestone: Callable = None,
        on_delete_milestone: Callable = None,
        on_add_stats: Callable = None,
        on_delete_stats: Callable = None,
    ):
        self.config = config
        self.state = state

        self._on_manual_death = on_manual_death
        self._on_timer_start = on_timer_start
        self._on_timer_stop = on_timer_stop
        self._on_timer_reset = on_timer_reset
        self._on_boss_start = on_boss_start
        self._on_boss_pause = on_boss_pause
        self._on_boss_resume = on_boss_resume
        self._on_boss_victory = on_boss_victory
        self._on_boss_cancel = on_boss_cancel
        self._on_toggle_detection = on_toggle_detection
        self._on_profile_select = on_profile_select
        self._on_capture = on_capture
        self._on_capture_region = on_capture_region
        self._on_test_detection = on_test_detection
        self._on_save_region = on_save_region
        self._on_quit = on_quit
        self._on_add_milestone = on_add_milestone or (lambda n, i: None)
        self._on_delete_milestone = on_delete_milestone or (lambda i: None)
        self._on_add_stats = on_add_stats or (lambda s: None)
        self._on_delete_stats = on_delete_stats or (lambda i: None)

        self.play_section: Optional[PlaySection] = None
        self.setup_section: Optional[SetupSection] = None
        self.history_section: Optional[HistorySection] = None
        self.compact_window: Optional[CompactWindow] = None

        self._current_section = "play"
        self._is_compact = False
        self._running = False

        self._sidebar_theme = None
        self._sidebar_active_theme = None
        self._sidebar_inactive_theme = None

    def _load_fonts(self):
        """Load fonts with Cyrillic support."""
        font_paths = []

        if sys.platform == 'darwin':
            font_paths = [
                '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
                '/System/Library/Fonts/Helvetica.ttc',
                '/Library/Fonts/Arial Unicode.ttf',
            ]
        elif sys.platform == 'win32':
            font_paths = [
                'C:/Windows/Fonts/arial.ttf',
                'C:/Windows/Fonts/segoeui.ttf',
                'C:/Windows/Fonts/tahoma.ttf',
            ]

        font_path = None
        for fp in font_paths:
            if Path(fp).exists():
                font_path = fp
                break

        if not font_path:
            return

        try:
            with dpg.font_registry():
                with dpg.font(font_path, 16) as font:
                    dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)
                    dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
                dpg.bind_font(font)
        except Exception:
            pass

    def init(self):
        """Initialize DearPyGui and create windows."""
        dpg.create_context()
        self._load_fonts()

        dpg.create_viewport(
            title="BB Death Detector",
            width=self.WIDTH,
            height=self.HEIGHT,
            resizable=False,
        )

        theme = create_theme()
        dpg.bind_theme(theme)

        self._sidebar_theme = create_sidebar_theme()
        self._sidebar_active_theme = create_sidebar_item_theme(active=True)
        self._sidebar_inactive_theme = create_sidebar_item_theme(active=False)

        self._create_main_window()

        self.compact_window = CompactWindow(
            on_expand=self._switch_to_full,
            on_boss_start=self._on_boss_start,
            on_boss_pause=self._on_boss_pause,
            on_boss_resume=self._on_boss_resume,
            on_boss_victory=self._on_boss_victory,
            on_boss_cancel=self._on_boss_cancel,
            on_add_milestone=self._on_add_milestone,
            on_add_stats=self._on_add_stats,
        )
        self.compact_window.create()

        self.state.subscribe(self._on_state_change)

        dpg.setup_dearpygui()
        dpg.show_viewport()
        self._running = True

    def _create_main_window(self):
        """Create the main window with sidebar layout."""
        with dpg.window(tag="main_window", label="", no_title_bar=True, no_resize=True, no_move=True):
            dpg.set_primary_window("main_window", True)

            # Header
            with dpg.group(horizontal=True):
                dpg.add_text("BB Death Detector", color=COLORS['text_primary'])
                dpg.add_spacer(width=350)
                dpg.add_button(label="[_]", width=30, callback=self._switch_to_compact)
                dpg.add_button(label="[X]", width=30, callback=self._on_quit)

            dpg.add_separator()

            # Main layout: Sidebar + Content
            with dpg.group(horizontal=True):
                # Sidebar
                with dpg.child_window(tag="sidebar", width=self.SIDEBAR_WIDTH, height=430, border=False):
                    dpg.bind_item_theme("sidebar", self._sidebar_theme)

                    dpg.add_spacer(height=10)

                    # Navigation buttons
                    btn_play = dpg.add_button(label="  Play", tag="nav_play", width=-1, height=35, callback=lambda: self._switch_section("play"))
                    dpg.bind_item_theme(btn_play, self._sidebar_active_theme)

                    dpg.add_spacer(height=5)

                    btn_setup = dpg.add_button(label="  Setup", tag="nav_setup", width=-1, height=35, callback=lambda: self._switch_section("setup"))
                    dpg.bind_item_theme(btn_setup, self._sidebar_inactive_theme)

                    dpg.add_spacer(height=5)

                    btn_history = dpg.add_button(label="  History", tag="nav_history", width=-1, height=35, callback=lambda: self._switch_section("history"))
                    dpg.bind_item_theme(btn_history, self._sidebar_inactive_theme)

                    # Spacer to push status to bottom
                    dpg.add_spacer(height=230)

                    # Status at bottom
                    dpg.add_separator()
                    dpg.add_spacer(height=5)
                    with dpg.group(horizontal=True):
                        dpg.add_text("●", tag="sidebar_status_dot", color=COLORS['red'])
                        dpg.add_text("Offline", tag="sidebar_status", color=COLORS['text_dim'])

                    dpg.add_text("", tag="sidebar_profile", color=COLORS['text_tertiary'])
                    dpg.add_button(label="Change Profile", width=-1, height=25, callback=self._show_profile_dialog)

                # Content area
                with dpg.child_window(tag="content_area", width=-1, height=430, border=False):
                    # Create sections
                    self.play_section = PlaySection(
                        on_manual_death=self._on_manual_death,
                        on_timer_start=self._on_timer_start,
                        on_timer_stop=self._on_timer_stop,
                        on_timer_reset=self._on_timer_reset,
                        on_boss_start=self._on_boss_start,
                        on_boss_pause=self._on_boss_pause,
                        on_boss_resume=self._on_boss_resume,
                        on_boss_victory=self._on_boss_victory,
                        on_boss_cancel=self._on_boss_cancel,
                        on_toggle_detection=self._on_toggle_detection,
                    )
                    self.play_section.create("content_area")

                    self.setup_section = SetupSection(
                        config=self.config,
                        on_capture=self._on_capture,
                        on_capture_region=self._on_capture_region,
                        on_test_detection=self._on_test_detection,
                        on_save_region=self._on_save_region,
                        on_save_settings=self._save_settings,
                    )
                    self.setup_section.create("content_area")

                    self.history_section = HistorySection(
                        on_add_milestone=self._on_add_milestone,
                        on_delete_milestone=self._on_delete_milestone,
                        on_add_stats=self._on_add_stats,
                        on_delete_stats=self._on_delete_stats,
                    )
                    self.history_section.create("content_area")

    def _switch_section(self, section: str):
        """Switch to a different section."""
        self._current_section = section

        # Update sidebar button themes
        sections = ["play", "setup", "history"]
        for s in sections:
            btn_tag = f"nav_{s}"
            if dpg.does_item_exist(btn_tag):
                if s == section:
                    dpg.bind_item_theme(btn_tag, self._sidebar_active_theme)
                else:
                    dpg.bind_item_theme(btn_tag, self._sidebar_inactive_theme)

        # Show/hide sections
        if self.play_section:
            if section == "play":
                self.play_section.show()
            else:
                self.play_section.hide()

        if self.setup_section:
            if section == "setup":
                self.setup_section.show()
            else:
                self.setup_section.hide()

        if self.history_section:
            if section == "history":
                self.history_section.show()
            else:
                self.history_section.hide()

    def show_profile_dialog(self):
        """Show profile selection dialog."""
        dialog = ProfileDialog(
            on_select=self._on_profile_selected,
            on_cancel=self._on_profile_cancel
        )
        dialog.show()

    def _show_profile_dialog(self):
        self.show_profile_dialog()

    def _on_profile_selected(self, name: str, password: str, is_new: bool):
        self._on_profile_select(name, password, is_new)

    def _on_profile_cancel(self):
        if not self.config.get('profile.name'):
            self._on_quit()

    def _save_settings(self, settings: dict):
        for key, value in settings.items():
            self.config.set(key, value)
        self.config.save()

    def _switch_to_compact(self):
        if dpg.does_item_exist("main_window"):
            dpg.configure_item("main_window", show=False)
        self.compact_window.show()
        self._is_compact = True

    def _switch_to_full(self):
        self.compact_window.hide()
        dpg.set_viewport_width(self.WIDTH)
        dpg.set_viewport_height(self.HEIGHT)
        if dpg.does_item_exist("main_window"):
            dpg.configure_item("main_window", show=True)
        self._is_compact = False

    def toggle_mode(self):
        if self._is_compact:
            self._switch_to_full()
        else:
            self._switch_to_compact()

    def on_f9_pressed(self):
        if self.setup_section:
            self.setup_section.on_f9_pressed()

    def _on_state_change(self, key: str, value):
        self._update_ui()

    def _update_ui(self):
        """Update all UI elements from state."""
        if self.play_section:
            self.play_section.update(
                deaths=self.state.deaths,
                elapsed=self.state.elapsed,
                is_running=self.state.is_running,
                boss_mode=self.state.boss_mode,
                boss_deaths=self.state.boss_deaths,
                boss_paused=self.state.boss_paused,
                detection_enabled=self.state.detection_enabled,
            )

        if self.setup_section:
            self.setup_section.update()

        if self.history_section:
            self.history_section.update(
                deaths=self.state.deaths,
                elapsed=self.state.elapsed,
                milestones=self.state.get('milestones', []),
                death_timestamps=self.state.get('death_timestamps', []),
                boss_fights=self.state.get('boss_fights', []),
                character_stats=self.state.get('character_stats', []),
            )

        if self.compact_window:
            self.compact_window.update(
                deaths=self.state.deaths,
                elapsed=self.state.elapsed,
                boss_mode=self.state.boss_mode,
                boss_deaths=self.state.boss_deaths,
                boss_paused=self.state.boss_paused,
                connected=self.state.connected,
                profile=self.state.profile_display_name or self.state.profile or "",
            )

        # Update sidebar status
        if dpg.does_item_exist("sidebar_status_dot"):
            dpg.configure_item("sidebar_status_dot", color=COLORS['green'] if self.state.connected else COLORS['red'])
        if dpg.does_item_exist("sidebar_status"):
            dpg.set_value("sidebar_status", "Online" if self.state.connected else "Offline")
        if dpg.does_item_exist("sidebar_profile"):
            dpg.set_value("sidebar_profile", self.state.profile_display_name or self.state.profile or "")

    def render(self):
        if self._running:
            if self.setup_section:
                self.setup_section.update()
            dpg.render_dearpygui_frame()

    def is_running(self) -> bool:
        return self._running and dpg.is_dearpygui_running()

    def destroy(self):
        self._running = False
        dpg.destroy_context()
```

**Step 2: Commit**

```bash
git add bb_detector/ui/app.py
git commit -m "feat(app): rewrite with sidebar navigation layout"
```

---

## Task 11: Update sections/__init__.py with Correct Imports

**Files:**
- Modify: `bb_detector/ui/sections/__init__.py`

**Step 1: Verify imports are correct**

The __init__.py was created in Task 1. Verify it works after all sections are created.

**Step 2: Commit (if changes needed)**

```bash
git add bb_detector/ui/sections/__init__.py
git commit -m "fix(sections): update imports"
```

---

## Task 12: Clean Up Old Tab Files

**Files:**
- Delete: `bb_detector/ui/tabs/play.py`
- Delete: `bb_detector/ui/tabs/settings.py`
- Delete: `bb_detector/ui/tabs/calibration.py`
- Delete: `bb_detector/ui/tabs/history.py`
- Delete: `bb_detector/ui/tabs/stats.py`
- Delete: `bb_detector/ui/tabs/__init__.py`

**Step 1: Remove old tabs directory**

```bash
rm -rf bb_detector/ui/tabs/
```

**Step 2: Commit**

```bash
git add -A
git commit -m "chore: remove old tabs directory (migrated to sections)"
```

---

## Task 13: Test the Application

**Step 1: Run the application**

```bash
cd /Users/warezzko/Desktop/netfl/bb-detector
source .venv/bin/activate
python -m bb_detector.main
```

**Step 2: Verify functionality**

- [ ] Application starts without errors
- [ ] Sidebar navigation works (Play/Setup/History)
- [ ] Play section shows deaths, timer, boss controls
- [ ] Setup section shows region selection, preview, settings
- [ ] History section shows milestones, stats, boss fights, deaths
- [ ] Compact mode works with boss controls and quick-add
- [ ] Profile dialog works

**Step 3: Fix any issues and commit**

```bash
git add -A
git commit -m "fix: resolve UI integration issues"
```

---

## Task 14: Final Release

**Step 1: Create release tag**

```bash
git tag v1.2.0
git push origin main
git push origin v1.2.0
```

**Step 2: Verify GitHub Actions builds successfully**

Check: https://github.com/m1ndfucker/autotracker/actions
