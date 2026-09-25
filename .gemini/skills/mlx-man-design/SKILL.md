---
name: mlx-man-design
description: Strict UI/UX design guidelines and visual aesthetics for the MLX-Man CLI application.
---

# MLX-Man UI/UX Design Guidelines

This skill defines the visual identity, UI components, and rendering patterns for MLX-Man. Any feature that interacts with the terminal (Presentation Layer) **MUST** strictly adhere to these guidelines.

## 1. The "Spotlight" Aesthetic
MLX-Man uses a floating, centered, macOS-native aesthetic, similar to Spotlight or Raycast. 
- **No manual clearing:** Never use `console.clear()` or ANSI escape sequences (`\033[H\033[2J`).
- **Central Rendering Engine:** Every view must be rendered by passing a `rich.console.Group` to `render_centered_view` from `mlx_man.cli_layout`. This engine handles terminal clearing, accurate vertical/horizontal centering, and the sticky footer.

```python
from mlx_man.cli_layout import render_centered_view
from rich.console import Group

# Correct:
layout = Group(header_panel, table, prompt_text)
render_centered_view(layout, prompt_lines=5)
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
- Always use `questionary` for user input (selectors, text inputs, confirmations).
- When calling `render_centered_view`, accurately estimate the `prompt_lines` argument based on how many choices `questionary` will render below the centered view. This ensures the entire block (content + prompt) is perfectly centered vertically.

## 5. UX Safety Guardrails
- **Destructive Actions:** Any action that modifies the system (deleting a model, killing a process) MUST have a mandatory `questionary.confirm` prompt.
- **Feedback:** After a long or destructive action, show a clear success or error message, and pause (via `time.sleep()` or waiting for the user to press Enter) so the user can read the result before the screen redraws.
- **Progress:** Long-running operations (like HuggingFace downloads) must provide continuous visual feedback (e.g., progress bars) so the user knows the app hasn't stalled.
