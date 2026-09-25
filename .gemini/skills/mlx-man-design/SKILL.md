---
name: mlx-man-design
description: Strict UI/UX design guidelines and visual aesthetics for the MLX-Man CLI application.
---

# MLX-Man UI/UX Design Guidelines

This skill defines the visual identity, UI components, and rendering patterns for MLX-Man. Any feature that interacts with the terminal (Presentation Layer) **MUST** strictly adhere to these guidelines.

## 1. The "Spotlight" Aesthetic
MLX-Man uses a floating, centered, macOS-native aesthetic, similar to Spotlight or Raycast. 
- **No manual clearing:** Never use `console.clear()` or ANSI escape sequences (`\033[H\033[2J`).
- **Central TUI Engine:** Every view must be rendered using `tui_engine.py` (`tui_select`, `tui_confirm`, `tui_text_input`). This engine uses `rich.live.Live(screen=True)` to take over the alternate screen buffer, meaning it naturally recalculates centering on every window resize event.

```python
from mlx_man.tui_engine import tui_select
from rich.console import Group

# Correct:
header_group = Group(header_panel, data_table)
choice = tui_select("Select action:", choices, format_func, header=header_group, footer="Status")
```

## 2. Color Palette
To maintain a professional, Apple-like aesthetic, avoid loud terminal colors.
- **Primary Borders & Panels:** `bright_black` (muted dark gray).
- **Primary Text:** `bold white` for headers, `white` for standard text.
- **Secondary Text:** `dim` (or `dim white`) for subtitles, descriptions, and metadata.
- **Semantic Accents (Use Sparingly):** 
  - `yellow` for cautions, warnings, or the "Most Used" trophy.
  - `red` for danger, destructive actions, or errors.
  - `green` for success or "safe" statuses.
  - *Do NOT use `cyan` or `magenta` for general structural borders.*

## 3. Reusable Components
Never instantiate `rich.panel.Panel` or `rich.table.Table` directly in your views. Always use the factory functions in `mlx_man.ui_components` to guarantee uniform styling.

### Headers and Info Panels
Use `create_header_panel(content, title)` for the main title of a screen or details of a model.
- Automatically applies `box.ROUNDED` and `bright_black` borders.

### Data Tables
Use `create_data_table(title, columns)` for lists of models, processes, etc.
- Automatically applies `dim white` headers and removes the outer box (`box=None`) for a cleaner look.

### Warnings and Feedback
Use `create_warning_panel(content, title)` for destructive confirmation prompts (like deleting a model or killing a process) or to show success/error feedback.
- Automatically applies `yellow` borders to grab attention.

## 4. Interactive Prompts
- **NEVER use `questionary` or `input()`.** Standard blocking input libraries cause screen tearing and disable dynamic resizing because they fight with the `Live` context.
- Always use the state-machine inputs from `mlx_man.tui_engine`:
  - `tui_select` for menus and lists.
  - `tui_confirm` for Yes/No prompts.
  - `tui_text_input` for typing text (like HuggingFace IDs).
- These functions use native non-blocking `termios` key captures, ensuring the `Live` renderer maintains total control of the layout matrix at all times.

## 5. UX Safety Guardrails
- **Destructive Actions:** Any action that modifies the system (deleting a model, killing a process) MUST have a mandatory `tui_confirm` prompt.
- **Feedback:** After a long or destructive action, show a clear success or error message, and pause (via `time.sleep()` or waiting for the user to press Enter) so the user can read the result before the screen redraws.
- **Progress:** Long-running operations (like HuggingFace downloads) must provide continuous visual feedback (e.g., progress bars) so the user knows the app hasn't stalled.
