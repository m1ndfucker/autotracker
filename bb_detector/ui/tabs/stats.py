# bb_detector/ui/tabs/stats.py
"""Stats tab - character stats tracking."""
import dearpygui.dearpygui as dpg
from typing import Callable, List
from ..theme import COLORS, create_accent_button_theme, create_success_button_theme
from ...state import CharacterStats


def format_time(ms: int) -> str:
    """Format milliseconds as HH:MM:SS."""
    total_seconds = ms // 1000
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


# Stat labels for Bloodborne
STAT_LABELS = [
    ('level', 'Level'),
    ('vitality', 'VIT'),
    ('endurance', 'END'),
    ('strength', 'STR'),
    ('skill', 'SKL'),
    ('bloodtinge', 'BLT'),
    ('arcane', 'ARC'),
]


class StatsTab:
    """Stats tab for character stats tracking."""

    def __init__(
        self,
        on_add_stats: Callable[[dict], None],
        on_delete_stats: Callable[[str], None],
    ):
        self.on_add_stats = on_add_stats
        self.on_delete_stats = on_delete_stats

        self._character_stats: List[CharacterStats] = []
        self._accent_theme = None
        self._success_theme = None

    def create(self, parent: int):
        """Create the Stats tab content."""
        self._accent_theme = create_accent_button_theme()
        self._success_theme = create_success_button_theme()

        with dpg.tab(label="Stats", parent=parent):
            dpg.add_text("Character Stats", color=COLORS['purple'])

            # Stats input form using table for proper layout
            with dpg.table(header_row=False, borders_innerH=False, borders_innerV=False,
                          borders_outerH=False, borders_outerV=False):
                # 4 columns: label, input, label, input
                dpg.add_table_column(width_fixed=True, init_width_or_weight=35)
                dpg.add_table_column(width_fixed=True, init_width_or_weight=70)
                dpg.add_table_column(width_fixed=True, init_width_or_weight=35)
                dpg.add_table_column(width_fixed=True, init_width_or_weight=70)

                # Row 1: LVL, VIT
                with dpg.table_row():
                    dpg.add_text("LVL", color=COLORS['text_dim'])
                    dpg.add_input_int(tag="stats_level", default_value=4, step=0)
                    dpg.add_text("VIT", color=COLORS['text_dim'])
                    dpg.add_input_int(tag="stats_vitality", default_value=9, step=0)

                # Row 2: END, STR
                with dpg.table_row():
                    dpg.add_text("END", color=COLORS['text_dim'])
                    dpg.add_input_int(tag="stats_endurance", default_value=9, step=0)
                    dpg.add_text("STR", color=COLORS['text_dim'])
                    dpg.add_input_int(tag="stats_strength", default_value=9, step=0)

                # Row 3: SKL, BLT
                with dpg.table_row():
                    dpg.add_text("SKL", color=COLORS['text_dim'])
                    dpg.add_input_int(tag="stats_skill", default_value=9, step=0)
                    dpg.add_text("BLT", color=COLORS['text_dim'])
                    dpg.add_input_int(tag="stats_bloodtinge", default_value=5, step=0)

                # Row 4: ARC, INS
                with dpg.table_row():
                    dpg.add_text("ARC", color=COLORS['text_dim'])
                    dpg.add_input_int(tag="stats_arcane", default_value=9, step=0)
                    dpg.add_text("INS", color=COLORS['text_dim'])
                    dpg.add_input_int(tag="stats_insight", default_value=0, step=0)

            # Echoes row
            with dpg.table(header_row=False, borders_innerH=False, borders_innerV=False,
                          borders_outerH=False, borders_outerV=False):
                dpg.add_table_column(width_fixed=True, init_width_or_weight=50)
                dpg.add_table_column(width_fixed=True, init_width_or_weight=120)

                with dpg.table_row():
                    dpg.add_text("Echoes", color=COLORS['text_dim'])
                    dpg.add_input_int(tag="stats_echoes", default_value=0, step=0)

            # Notes + Save row
            with dpg.table(header_row=False, borders_innerH=False, borders_innerV=False,
                          borders_outerH=False, borders_outerV=False):
                dpg.add_table_column(width_stretch=True)
                dpg.add_table_column(width_fixed=True, init_width_or_weight=60)

                with dpg.table_row():
                    dpg.add_input_text(tag="stats_notes", hint="Notes...")
                    btn = dpg.add_button(label="Save", callback=self._on_add_stats)
                    dpg.bind_item_theme(btn, self._success_theme)

            dpg.add_separator()

            # Stats history
            dpg.add_text("History", color=COLORS['text_dim'])
            with dpg.child_window(tag="stats_list", height=120, border=False):
                dpg.add_text("No stats recorded", tag="no_stats_text", color=COLORS['text_dim'])

    def update(self, character_stats: List[CharacterStats]):
        """Update stats display."""
        self._character_stats = character_stats
        self._update_stats_list()

    def _update_stats_list(self):
        """Update stats list display."""
        if not dpg.does_item_exist("stats_list"):
            return

        # Clear existing items
        children = dpg.get_item_children("stats_list", 1)
        if children:
            for child in children:
                dpg.delete_item(child)

        if not self._character_stats:
            dpg.add_text(
                "No stats recorded",
                parent="stats_list",
                color=COLORS['text_dim']
            )
            return

        # Add stats (most recent first)
        for stats in reversed(self._character_stats[-10:]):
            with dpg.group(parent="stats_list"):
                # First row: time and level
                with dpg.group(horizontal=True):
                    dpg.add_text(f"@ {format_time(stats.timestamp)}", color=COLORS['text_dim'])
                    dpg.add_text(f"LVL {stats.level}", color=COLORS['purple'])
                    dpg.add_button(
                        label="x",
                        width=20,
                        user_data=stats.id,
                        callback=self._on_delete_stats_click
                    )

                # Second row: main stats
                with dpg.group(horizontal=True):
                    dpg.add_text(
                        f"VIT:{stats.vitality} END:{stats.endurance} STR:{stats.strength} SKL:{stats.skill} BLT:{stats.bloodtinge} ARC:{stats.arcane}",
                        color=COLORS['text_secondary']
                    )

                # Third row: echoes/insight/notes
                if stats.blood_echoes > 0 or stats.insight > 0 or stats.notes:
                    with dpg.group(horizontal=True):
                        if stats.blood_echoes > 0:
                            dpg.add_text(f"Echoes: {stats.blood_echoes:,}", color=COLORS['amber'])
                        if stats.insight > 0:
                            dpg.add_text(f"Insight: {stats.insight}", color=COLORS['teal'])
                        if stats.notes:
                            dpg.add_text(f'"{stats.notes}"', color=COLORS['text_dim'])

                dpg.add_separator()

    def _on_add_stats(self):
        """Handle add stats button."""
        stats = {
            'level': dpg.get_value("stats_level") if dpg.does_item_exist("stats_level") else 4,
            'vitality': dpg.get_value("stats_vitality") if dpg.does_item_exist("stats_vitality") else 9,
            'endurance': dpg.get_value("stats_endurance") if dpg.does_item_exist("stats_endurance") else 9,
            'strength': dpg.get_value("stats_strength") if dpg.does_item_exist("stats_strength") else 9,
            'skill': dpg.get_value("stats_skill") if dpg.does_item_exist("stats_skill") else 9,
            'bloodtinge': dpg.get_value("stats_bloodtinge") if dpg.does_item_exist("stats_bloodtinge") else 5,
            'arcane': dpg.get_value("stats_arcane") if dpg.does_item_exist("stats_arcane") else 9,
            'bloodEchoes': dpg.get_value("stats_echoes") if dpg.does_item_exist("stats_echoes") else 0,
            'insight': dpg.get_value("stats_insight") if dpg.does_item_exist("stats_insight") else 0,
            'notes': dpg.get_value("stats_notes") if dpg.does_item_exist("stats_notes") else '',
        }

        self.on_add_stats(stats)

        # Clear notes
        if dpg.does_item_exist("stats_notes"):
            dpg.set_value("stats_notes", "")

    def _on_delete_stats_click(self, sender, app_data, user_data):
        """Handle delete stats button."""
        stats_id = user_data
        if stats_id:
            self.on_delete_stats(stats_id)
