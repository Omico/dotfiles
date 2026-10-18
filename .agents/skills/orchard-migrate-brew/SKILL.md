---
name: orchard-migrate-brew
description: "Use for Homebrew-to-Orchard migration or cask package authoring, including GitHub cask lookup when local brew is unavailable."
---

# Orchard: migrate from Homebrew

## Overview

This skill guides **`orchard migrate brew`** flows for macOS GUI apps that are currently installed via Homebrew casks and should be managed by Orchard instead. It covers both **global dry-run plans** and **targeted cask handling**, including authoring new `home/dot_config/exact_orchard/exact_apps/<app_id>.fish` packages when no Orchard package exists yet.

Use the `orchard` skill for package format, helpers, and quality checks. Read its `references/app-package-format.md` for cask mapping.

---

## When not to use

- Editing an existing Orchard package without any Homebrew migration context — use the `orchard` skill only
- General fish scripting or shell tooling that is unrelated to Orchard or Homebrew casks

---

## Select the workflow

- **Inputs**
  - Empty or very short message after invoking this skill → treat as a request for a **global migration review** (dry-run plan first)
  - One or more explicit cask names, or a request to **author Orchard packages** → treat as a **targeted cask / package-authoring** request

---

## Global migration workflow (no specific casks)

- Run `orchard migrate brew --plan` under the shared safety requirements below
- Summarize for the user:
  - Outdated casks that **can** migrate because an Orchard package already exists
  - Outdated casks that **cannot** migrate yet because no Orchard package exists
- If **no** outdated casks can migrate, explain that there is nothing to do and stop without asking for confirmation
- If some casks **can** migrate:
  - Apply the shared confirmation requirement: ask whether to uninstall those Homebrew casks and reinstall them via Orchard
  - If the user confirms:
    - Run `orchard migrate brew`
    - Show a concise summary of what migrated and any failures
  - If the user declines:
    - Do not run the real migration
    - Offer to help author Orchard packages for specific casks that are still missing Orchard packages

---

## Targeted cask / package-authoring workflow

- Parse cask names from the user’s message
- For each cask:
  - Check whether `home/dot_config/exact_orchard/exact_apps/<cask>.fish` already exists
  - If a package exists:
    - Explain what `orchard migrate brew --plan` would show for that context, or suggest using `orchard install <app_id>` directly if migration is unnecessary
  - If no package exists:
    - Enter Orchard package authoring mode:
      - Ask for any missing details (homepage, download URL, special install behavior)
      - Prefer `brew info --cask <cask>` when local `brew` is available; otherwise use the GitHub API to read the cask file from `Homebrew/homebrew-cask` and extract homepage, download URL, and install details
      - Follow the `orchard` skill and **`app-package-format`** reference to draft `home/dot_config/exact_orchard/exact_apps/<cask>.fish`
    - Write the Orchard app package directly to `home/dot_config/exact_orchard/exact_apps/<cask>.fish` based on the user’s request, without asking for extra confirmation

---

## Safety and conventions

- **Never** run `brew` commands that remove or modify casks without explicit user confirmation
- Keep comments and user-visible strings in Orchard-related scripts in **English** (follow workspace rules)
- Run `orchard migrate brew --plan` and `orchard migrate brew` only in the user’s real environment when their Homebrew state must be accurate
- Prefer concise summaries over full command output unless the user explicitly asks for detailed logs

---

## Checklist before finishing

- **Migration safety**
  - Keep plans within the requested scope and migrations within the explicitly confirmed scope
- **Package quality**
  - New or edited packages follow the `orchard` skill and **development-guidelines** checklist
- **User reminders**
  - After any package change, remind the user to run `chezmoi apply`, then `orchard list` and `orchard install <app_id>` as appropriate
