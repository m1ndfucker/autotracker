# bb_detector/ui/sections/history.py
"""History section - merged history + stats for sidebar navigation."""
import dearpygui.dearpygui as dpg
from typing import Callable, List, Optional
from ..theme import (
    COLORS,
    create_accent_button_theme,
    create_section_card_theme,
)
from ..dialogs.milestone import MilestoneDialog
from ..dialogs.stats import StatsDialog
from ...state import Milestone, DeathTimestamp, BossFight, CharacterStats


def format_time(ms: int) -> str:
    """Format milliseconds as HH:MM:SS."""
    total_seconds = ms // 1000
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


class HistorySection:
    """History section with session summary, milestones, stats, boss fights, and deaths."""

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

        self._deaths: int = 0
        self._elapsed: int = 0

        self._accent_theme: Optional[int] = None
        self._card_theme: Optional[int] = None
        self._container_tag = "history_section_container"

        self._milestone_dialog: Optional[MilestoneDialog] = None
        self._stats_dialog: Optional[StatsDialog] = None

    def create(self, parent: str):
        """Create the History section content."""
        self._accent_theme = create_accent_button_theme()
        self._card_theme = create_section_card_theme()

        with dpg.child_window(
            tag=self._container_tag,
            parent=parent,
            border=False,
            autosize_x=True,
            autosize_y=True,
        ):
            # === Current Session Card ===
            with dpg.child_window(height=80, border=True) as card:
                dpg.bind_item_theme(card, self._card_theme)

                dpg.add_text("Current Session", color=COLORS['text_primary'])
                dpg.add_spacer(height=2)

                with dpg.group(horizontal=True):
                    # Deaths
                    dpg.add_text("Deaths:", color=COLORS['text_tertiary'])
                    dpg.add_text("0", tag="history_session_deaths", color=COLORS['red'])
                    dpg.add_spacer(width=15)

                    # Time
                    dpg.add_text("Time:", color=COLORS['text_tertiary'])
                    dpg.add_text("0:00:00", tag="history_session_time", color=COLORS['text_secondary'])

                with dpg.group(horizontal=True):
                    # Bosses
                    dpg.add_text("Bosses:", color=COLORS['text_tertiary'])
                    dpg.add_text("0", tag="history_session_bosses", color=COLORS['teal'])
                    dpg.add_spacer(width=15)

                    # Milestones
                    dpg.add_text("Milestones:", color=COLORS['text_tertiary'])
                    dpg.add_text("0", tag="history_session_milestones", color=COLORS['purple'])

            dpg.add_spacer(height=5)

            # === Milestones Section ===
            with dpg.group(horizontal=True):
                dpg.add_text("Milestones", color=COLORS['purple'])
                dpg.add_spacer(width=-1)
                btn = dpg.add_button(label="+ Add", width=60, callback=self._on_add_milestone_click)
                dpg.bind_item_theme(btn, self._accent_theme)

            with dpg.child_window(tag="history_milestones_list", height=70, border=False):
                dpg.add_text("No milestones yet", tag="history_no_milestones", color=COLORS['text_tertiary'])

            dpg.add_spacer(height=5)

            # === Character Stats Section ===
            with dpg.group(horizontal=True):
                dpg.add_text("Character Stats", color=COLORS['purple'])
                dpg.add_spacer(width=-1)
                btn = dpg.add_button(label="+ Add", width=60, callback=self._on_add_stats_click)
                dpg.bind_item_theme(btn, self._accent_theme)

            with dpg.child_window(tag="history_stats_list", height=50, border=False):
                dpg.add_text("No stats recorded", tag="history_no_stats", color=COLORS['text_tertiary'])

            dpg.add_spacer(height=5)
            dpg.add_separator()
            dpg.add_spacer(height=5)

            # === Boss Fights Section (auto-recorded) ===
            dpg.add_text("Boss Fights", color=COLORS['teal'])

            with dpg.child_window(tag="history_bosses_list", height=60, border=False):
                dpg.add_text("No boss fights yet", tag="history_no_bosses", color=COLORS['text_tertiary'])

            dpg.add_spacer(height=5)

            # === Recent Deaths Section (auto-recorded) ===
            dpg.add_text("Recent Deaths", color=COLORS['red'])

            with dpg.child_window(tag="history_deaths_list", height=50, border=False):
                dpg.add_text("No deaths recorded", tag="history_no_deaths", color=COLORS['text_tertiary'])

    def update(
        self,
        deaths: int,
        elapsed: int,
        milestones: List[Milestone],
        death_timestamps: List[DeathTimestamp],
        boss_fights: List[BossFight],
        character_stats: List[CharacterStats],
    ):
        """Update all displays."""
        self._deaths = deaths
        self._elapsed = elapsed
        self._milestones = milestones
        self._death_timestamps = death_timestamps
        self._boss_fights = boss_fights
        self._character_stats = character_stats

        self._update_session_card()
        self._update_milestones_list()
        self._update_stats_list()
        self._update_bosses_list()
        self._update_deaths_list()

    def show(self):
        """Show the history section."""
        if dpg.does_item_exist(self._container_tag):
            dpg.show_item(self._container_tag)

    def hide(self):
        """Hide the history section."""
        if dpg.does_item_exist(self._container_tag):
            dpg.hide_item(self._container_tag)

    def _update_session_card(self):
        """Update the current session summary card."""
        if dpg.does_item_exist("history_session_deaths"):
            dpg.set_value("history_session_deaths", str(self._deaths))

        if dpg.does_item_exist("history_session_time"):
            dpg.set_value("history_session_time", format_time(self._elapsed))

        if dpg.does_item_exist("history_session_bosses"):
            dpg.set_value("history_session_bosses", str(len(self._boss_fights)))

        if dpg.does_item_exist("history_session_milestones"):
            dpg.set_value("history_session_milestones", str(len(self._milestones)))

    def _update_milestones_list(self):
        """Update milestones display."""
        if not dpg.does_item_exist("history_milestones_list"):
            return

        # Clear existing items
        children = dpg.get_item_children("history_milestones_list", 1)
        if children:
            for child in children:
                dpg.delete_item(child)

        if not self._milestones:
            dpg.add_text(
                "No milestones yet",
                parent="history_milestones_list",
                color=COLORS['text_tertiary']
            )
            return

        # Add milestones (most recent first)
        for milestone in reversed(self._milestones[-10:]):
            with dpg.group(horizontal=True, parent="history_milestones_list"):
                dpg.add_text(milestone.icon, color=COLORS['purple'])
                dpg.add_text(milestone.name, color=COLORS['text_primary'])
                dpg.add_text(f"@ {format_time(milestone.timestamp)}", color=COLORS['text_tertiary'])
                dpg.add_button(
                    label="x",
                    width=20,
                    user_data=milestone.id,
                    callback=self._on_delete_milestone_click
                )

    def _update_stats_list(self):
        """Update character stats display."""
        if not dpg.does_item_exist("history_stats_list"):
            return

        # Clear existing items
        children = dpg.get_item_children("history_stats_list", 1)
        if children:
            for child in children:
                dpg.delete_item(child)

        if not self._character_stats:
            dpg.add_text(
                "No stats recorded",
                parent="history_stats_list",
                color=COLORS['text_tertiary']
            )
            return

        # Add stats (most recent first)
        for stats in reversed(self._character_stats[-5:]):
            with dpg.group(parent="history_stats_list"):
                # First row: time and level
                with dpg.group(horizontal=True):
                    dpg.add_text(f"@ {format_time(stats.timestamp)}", color=COLORS['text_tertiary'])
                    dpg.add_text(f"LVL {stats.level}", color=COLORS['purple'])
                    dpg.add_button(
                        label="x",
                        width=20,
                        user_data=stats.id,
                        callback=self._on_delete_stats_click
                    )

                # Second row: main stats (compact format)
                with dpg.group(horizontal=True):
                    dpg.add_text(
                        f"V{stats.vitality} E{stats.endurance} S{stats.strength} K{stats.skill} B{stats.bloodtinge} A{stats.arcane}",
                        color=COLORS['text_secondary']
                    )

                dpg.add_spacer(height=2)

    def _update_bosses_list(self):
        """Update boss fights display."""
        if not dpg.does_item_exist("history_bosses_list"):
            return

        # Clear existing items
        children = dpg.get_item_children("history_bosses_list", 1)
        if children:
            for child in children:
                dpg.delete_item(child)

        if not self._boss_fights:
            dpg.add_text(
                "No boss fights yet",
                parent="history_bosses_list",
                color=COLORS['text_tertiary']
            )
            return

        # Add boss fights (most recent first)
        for boss in reversed(self._boss_fights[-5:]):
            with dpg.group(horizontal=True, parent="history_bosses_list"):
                dpg.add_text(boss.name or "Unknown", color=COLORS['teal'])
                dpg.add_text(f"{boss.deaths_on_boss} deaths", color=COLORS['red'])
                dpg.add_text(f"({format_time(boss.duration)})", color=COLORS['text_tertiary'])

    def _update_deaths_list(self):
        """Update recent deaths display."""
        if not dpg.does_item_exist("history_deaths_list"):
            return

        # Clear existing items
        children = dpg.get_item_children("history_deaths_list", 1)
        if children:
            for child in children:
                dpg.delete_item(child)

        if not self._death_timestamps:
            dpg.add_text(
                "No deaths recorded",
                parent="history_deaths_list",
                color=COLORS['text_tertiary']
            )
            return

        # Add deaths (most recent first)
        for death in reversed(self._death_timestamps[-10:]):
            with dpg.group(horizontal=True, parent="history_deaths_list"):
                dpg.add_text(f"#{death.death_number}", color=COLORS['red'])
                dpg.add_text(f"@ {format_time(death.timestamp)}", color=COLORS['text_tertiary'])

    def _on_add_milestone_click(self):
        """Show milestone dialog."""
        self._milestone_dialog = MilestoneDialog(
            on_add=self.on_add_milestone,
            on_cancel=lambda: None
        )
        self._milestone_dialog.show()

    def _on_delete_milestone_click(self, sender, app_data, user_data):
        """Handle delete milestone button."""
        milestone_id = user_data
        if milestone_id:
            self.on_delete_milestone(milestone_id)

    def _on_add_stats_click(self):
        """Show stats dialog."""
        self._stats_dialog = StatsDialog(
            on_add=self.on_add_stats,
            on_cancel=lambda: None
        )
        self._stats_dialog.show()

    def _on_delete_stats_click(self, sender, app_data, user_data):
        """Handle delete stats button."""
        stats_id = user_data
        if stats_id:
            self.on_delete_stats(stats_id)
