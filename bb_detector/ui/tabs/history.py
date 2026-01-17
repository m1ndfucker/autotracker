# bb_detector/ui/tabs/history.py
"""History tab - milestones, deaths, and boss fights."""
import dearpygui.dearpygui as dpg
from typing import Callable, List
from ..theme import COLORS, create_accent_button_theme, create_success_button_theme
from ...state import Milestone, DeathTimestamp, BossFight


# Icons for milestone picker
MILESTONE_ICONS = ['★', '⚑', '🔑', '💎', '🗡️', '📍', '🏆', '🎯']


def format_time(ms: int) -> str:
    """Format milliseconds as HH:MM:SS."""
    total_seconds = ms // 1000
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


class HistoryTab:
    """History tab with milestones, deaths, and boss fights."""

    def __init__(
        self,
        on_add_milestone: Callable[[str, str], None],
        on_delete_milestone: Callable[[str], None],
    ):
        self.on_add_milestone = on_add_milestone
        self.on_delete_milestone = on_delete_milestone

        self._milestones: List[Milestone] = []
        self._death_timestamps: List[DeathTimestamp] = []
        self._boss_fights: List[BossFight] = []

        self._selected_icon = '★'
        self._accent_theme = None
        self._success_theme = None

    def create(self, parent: int):
        """Create the History tab content."""
        self._accent_theme = create_accent_button_theme()
        self._success_theme = create_success_button_theme()

        with dpg.tab(label="History", parent=parent):
            # Milestones section
            dpg.add_text("Milestones", color=COLORS['purple'])

            # Add milestone row
            with dpg.group(horizontal=True):
                dpg.add_input_text(
                    tag="milestone_input",
                    hint="Milestone name...",
                    width=150,
                    on_enter=True,
                    callback=self._on_add_milestone
                )
                dpg.add_combo(
                    MILESTONE_ICONS,
                    tag="milestone_icon_combo",
                    default_value='★',
                    width=50,
                    callback=self._on_icon_change
                )
                btn = dpg.add_button(
                    label="+",
                    callback=self._on_add_milestone,
                    width=30
                )
                dpg.bind_item_theme(btn, self._accent_theme)

            # Milestones list
            with dpg.child_window(tag="milestones_list", height=100, border=False):
                dpg.add_text("No milestones yet", tag="no_milestones_text", color=COLORS['text_dim'])

            dpg.add_separator()

            # Deaths section
            dpg.add_text("Recent Deaths", color=COLORS['red'])

            with dpg.child_window(tag="deaths_list", height=80, border=False):
                dpg.add_text("No deaths recorded", tag="no_deaths_text", color=COLORS['text_dim'])

            dpg.add_separator()

            # Boss fights section
            dpg.add_text("Boss Fights", color=COLORS['teal'])

            with dpg.child_window(tag="bosses_list", height=80, border=False):
                dpg.add_text("No boss fights yet", tag="no_bosses_text", color=COLORS['text_dim'])

    def update(
        self,
        milestones: List[Milestone],
        death_timestamps: List[DeathTimestamp],
        boss_fights: List[BossFight]
    ):
        """Update all lists."""
        self._milestones = milestones
        self._death_timestamps = death_timestamps
        self._boss_fights = boss_fights

        self._update_milestones_list()
        self._update_deaths_list()
        self._update_bosses_list()

    def _update_milestones_list(self):
        """Update milestones display."""
        if not dpg.does_item_exist("milestones_list"):
            return

        # Clear existing items
        children = dpg.get_item_children("milestones_list", 1)
        if children:
            for child in children:
                dpg.delete_item(child)

        if not self._milestones:
            dpg.add_text(
                "No milestones yet",
                parent="milestones_list",
                color=COLORS['text_dim']
            )
            return

        # Add milestones (most recent first)
        for milestone in reversed(self._milestones[-10:]):  # Show last 10
            with dpg.group(horizontal=True, parent="milestones_list"):
                dpg.add_text(milestone.icon, color=COLORS['purple'])
                dpg.add_text(
                    f"{milestone.name}",
                    color=COLORS['text']
                )
                dpg.add_text(
                    f"@ {format_time(milestone.timestamp)}",
                    color=COLORS['text_dim']
                )
                dpg.add_button(
                    label="x",
                    width=20,
                    user_data=milestone.id,
                    callback=self._on_delete_milestone_click
                )

    def _update_deaths_list(self):
        """Update deaths display."""
        if not dpg.does_item_exist("deaths_list"):
            return

        # Clear existing items
        children = dpg.get_item_children("deaths_list", 1)
        if children:
            for child in children:
                dpg.delete_item(child)

        if not self._death_timestamps:
            dpg.add_text(
                "No deaths recorded",
                parent="deaths_list",
                color=COLORS['text_dim']
            )
            return

        # Add deaths (most recent first)
        for death in reversed(self._death_timestamps[-10:]):  # Show last 10
            with dpg.group(horizontal=True, parent="deaths_list"):
                dpg.add_text(f"#{death.death_number}", color=COLORS['red'])
                dpg.add_text(
                    f"@ {format_time(death.timestamp)}",
                    color=COLORS['text_dim']
                )

    def _update_bosses_list(self):
        """Update boss fights display."""
        if not dpg.does_item_exist("bosses_list"):
            return

        # Clear existing items
        children = dpg.get_item_children("bosses_list", 1)
        if children:
            for child in children:
                dpg.delete_item(child)

        if not self._boss_fights:
            dpg.add_text(
                "No boss fights yet",
                parent="bosses_list",
                color=COLORS['text_dim']
            )
            return

        # Add boss fights (most recent first)
        for boss in reversed(self._boss_fights[-5:]):  # Show last 5
            with dpg.group(horizontal=True, parent="bosses_list"):
                dpg.add_text(
                    boss.name or "Unknown",
                    color=COLORS['teal']
                )
                dpg.add_text(
                    f"{boss.deaths_on_boss} deaths",
                    color=COLORS['red']
                )
                dpg.add_text(
                    f"({format_time(boss.duration)})",
                    color=COLORS['text_dim']
                )

    def _on_icon_change(self, sender, app_data):
        """Handle icon selection change."""
        self._selected_icon = app_data

    def _on_add_milestone(self, sender=None, app_data=None):
        """Handle add milestone button."""
        if not dpg.does_item_exist("milestone_input"):
            return

        name = dpg.get_value("milestone_input").strip()
        if not name:
            return

        icon = dpg.get_value("milestone_icon_combo") if dpg.does_item_exist("milestone_icon_combo") else '★'

        self.on_add_milestone(name, icon)

        # Clear input
        dpg.set_value("milestone_input", "")

    def _on_delete_milestone_click(self, sender, app_data, user_data):
        """Handle delete milestone button."""
        milestone_id = user_data
        if milestone_id:
            self.on_delete_milestone(milestone_id)
