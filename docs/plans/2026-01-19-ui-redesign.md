# BB Death Detector UI Redesign

## Overview

Professional UI redesign with sidebar navigation, improved visual hierarchy, and better compact mode.

## Requirements

1. **Window size**: 600x500 (was 400x520)
2. **Navigation**: Sidebar with 3 sections (was 5 tabs)
3. **Visual hierarchy**: Card-based layout with clear sections
4. **Compact mode**: 280x160 with full boss controls + quick add buttons

## Main Window Layout

```
┌─────────────────────────────────────────────────────┐
│  BB Death Detector                        [_] [X]  │  <- Header 30px
├────────────┬────────────────────────────────────────┤
│            │                                        │
│  ▶ Play    │         Content Area                  │
│            │         (440px wide)                   │
│  ⚙ Setup   │                                        │
│            │                                        │
│  📊 History│                                        │
│            │                                        │
│────────────│                                        │
│  ● Online  │                                        │
│  warezz    │                                        │
└────────────┴────────────────────────────────────────┘
   150px                    450px
```

## Sections

### Play Section (Main)

- Deaths counter: 64px red number, centered
- Timer card: time display + Start/Stop/Reset buttons
- Boss card: status + controls (Start/Victory/Pause/Cancel)
- Detection card: ON/OFF toggle

Content fits in 440px height without scroll.

### Setup Section

Scrollable content with 4 cards:

1. **Detection Region**: window name, region %, Select/F9/Clear buttons
2. **Test & Preview**: 200x112 preview image, Capture/Live Preview buttons
3. **Detection Settings**: Monitor, Game, Cooldown dropdowns
4. **Hotkeys**: Manual Death, Toggle Boss, Toggle Mode, Pause Detect

Total height ~480px, needs scroll.

### History Section

Scrollable content with separator:

1. **Current Session**: summary stats (deaths, time, bosses, milestones)
2. **Milestones**: scrollable list + Add button
3. **Character Stats**: scrollable list + Add button
4. --- SEPARATOR ---
5. **Boss Fights**: scrollable list (auto-recorded)
6. **Recent Deaths**: scrollable list (auto-recorded)

## Compact Mode

Size: 280x160px, always on top, draggable

```
┌────────────────────────────────────────┐
│  ☠ 42          03:42:15          [◱]  │
├────────────────────────────────────────┤
│  👹 BOSS ACTIVE           Deaths: 3   │
│  [Victory]  [Pause]  [Cancel]         │
├────────────────────────────────────────┤
│  [+ Milestone]        [+ Stats]       │
│  ● Online                    warezz   │
└────────────────────────────────────────┘
```

Boss states:
- Inactive: gray bg, [Start Boss] button
- Active: purple bg, [Victory][Pause][Cancel]
- Paused: amber bg, [Victory][Resume][Cancel]

## File Structure

```
ui/
├── app.py              # Sidebar layout
├── theme.py            # Updated theme + card styles
├── compact.py          # Updated compact mode
├── sections/
│   ├── __init__.py
│   ├── play.py         # Deaths, timer, boss, detection
│   ├── setup.py        # Region + settings + hotkeys
│   └── history.py      # Milestones, stats, bosses, deaths
└── dialogs/
    ├── __init__.py
    ├── profile.py      # Profile selection (moved)
    ├── milestone.py    # Add milestone modal
    └── stats.py        # Add stats modal
```

## Migration Plan

| Old File | Action |
|----------|--------|
| `ui/tabs/play.py` | → `ui/sections/play.py` (rewrite) |
| `ui/tabs/settings.py` | Merge into `ui/sections/setup.py` |
| `ui/tabs/calibration.py` | Merge into `ui/sections/setup.py` |
| `ui/tabs/history.py` | Merge into `ui/sections/history.py` |
| `ui/tabs/stats.py` | Merge into `ui/sections/history.py` |
| `ui/profile_dialog.py` | → `ui/dialogs/profile.py` |
| `ui/compact.py` | Rewrite with new layout |
| `ui/app.py` | Rewrite with sidebar |

## Sizing Constraints

- Main window: 600x500 (not resizable)
- Sidebar: 150px wide
- Content area: 450px wide, 440px usable with padding
- Cards: 400px wide, 12px padding, 8px border-radius
- Scrollable lists: max-height 80-120px each
- Compact window: 280x160

## Theme Updates

New card theme for sections:
- Background: `bg_secondary`
- Border: `border_subtle`
- Padding: 12px
- Border-radius: 8px

Sidebar active state:
- Left border: 3px red accent
- Background: slightly elevated
