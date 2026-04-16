---
name: orchard-add-package
description: Use when adding a new Orchard app package so orchard list and orchard install can manage a macOS app.
---

# Orchard: add package

## Purpose

Create a new **`home/dot_config/orchard/apps/<app_id>.fish`** package so `orchard list` / `orchard install` can manage the app.

## Behavior

- **Read and follow** the **Orchard** agent skill (`.cursor/skills/orchard/SKILL.md` and its references) for workflow, format, checklists, and conventions.
- Use the user’s message (app name, `app_id`, URL, cask, GitHub repo, etc.) as input.
