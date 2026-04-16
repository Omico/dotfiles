---
name: orchard-migrate-brew
description: Use when migrating installed Homebrew casks to Orchard app packages or authoring Orchard packages for specific casks, including when local brew is unavailable and cask details must come from the GitHub cask repository.
---

# Orchard: migrate from Homebrew

## Overview

This skill guides **`orchard migrate brew`** flows for macOS GUI apps that are currently installed via Homebrew casks and should be managed by Orchard instead.
It covers both **global dry-run plans** and **targeted cask handling**, including authoring new `home/dot_config/orchard/apps/<app_id>.fish` packages when no Orchard package exists yet.

For app package format, helpers, and quality bar, always use the **`orchard`** skill as the primary reference — [SKILL.md](../orchard/SKILL.md) and [references/app-package-format.md](../orchard/references/app-package-format.md).

---

## When to use this skill

- User wants to migrate one or more Homebrew casks to Orchard or asks to run **`orchard migrate brew`**
- User requests a **dry-run** migration plan with **`orchard migrate brew --plan`**
- User names specific casks and wants help migrating them or creating Orchard packages for apps that are still cask-only
- Local `brew` may be unavailable (e.g. sandbox) and cask details must come from the **`Homebrew/homebrew-cask`** GitHub repository instead

## When not to use

- Editing an existing Orchard package without any Homebrew migration context — use the **`orchard`** skill only
- General fish scripting or shell tooling that is unrelated to Orchard or Homebrew casks

---

## Inputs and outputs

- **Inputs**
  - Empty or very short message after invoking this skill → treat as a request for a **global migration review** (dry-run plan first)
  - One or more explicit cask names, or a request to **author Orchard packages** → treat as a **targeted cask / package-authoring** request

- **Outputs**
  - Summary of outdated casks that **can** migrate (Orchard package exists) vs those that **cannot yet** (no Orchard package)
  - After confirmation: result summary for `orchard migrate brew` (successes and failures only, not full logs unless requested)
  - For authoring flows: new or updated `home/dot_config/orchard/apps/<cask>.fish` plus reminders to run `chezmoi apply` and `orchard install <app_id>`

---

## Global migration workflow (no specific casks)

- Run `orchard migrate brew --plan` in the user’s **real** environment so Homebrew state is accurate
- Summarize for the user:
  - Outdated casks that **can** migrate because an Orchard package already exists
  - Outdated casks that **cannot** migrate yet because no Orchard package exists
- If **no** outdated casks can migrate, explain that there is nothing to do and stop without asking for confirmation
- If some casks **can** migrate:
  - Ask for explicit confirmation before making destructive changes, for example:
    - “Do you want me to run `orchard migrate brew` now to uninstall those Homebrew casks and reinstall them via Orchard?”
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
  - Check whether `home/dot_config/orchard/apps/<cask>.fish` already exists
  - If a package exists:
    - Explain what `orchard migrate brew --plan` would show for that context, or suggest using `orchard install <app_id>` directly if migration is unnecessary
  - If no package exists:
    - Enter Orchard package authoring mode:
      - Ask for any missing details (homepage, download URL, special install behavior)
      - Prefer `brew info --cask <cask>` when local `brew` is available; otherwise use the GitHub API to read the cask file from `Homebrew/homebrew-cask` and extract homepage, download URL, and install details
      - Follow the **`orchard`** skill and **`app-package-format`** reference to draft `home/dot_config/orchard/apps/<cask>.fish`
    - Write the Orchard app package directly to `home/dot_config/orchard/apps/<cask>.fish` based on the user’s request, without asking for extra confirmation
- After any package change, remind the user to:
  - Run `chezmoi apply`
  - Run `orchard list` and `orchard install <app_id>` as appropriate

---

## Safety and conventions

- **Never** run `brew` commands that remove or modify casks without explicit user confirmation
- Keep comments and user-visible strings in Orchard-related scripts in **English** (follow workspace rules)
- Run `orchard migrate brew --plan` and `orchard migrate brew` only in the user’s real environment when their Homebrew state must be accurate
- Prefer concise summaries over full command output unless the user explicitly asks for detailed logs

---

## Checklist before finishing

- **Migration safety**
  - Migration or plan matches what the user explicitly confirmed
  - No destructive `brew` actions were taken without a clear yes/no confirmation
- **Package quality**
  - New or edited packages follow the **`orchard`** skill and **development-guidelines** checklist
- **User reminders**
  - User has been reminded to run `chezmoi apply`
  - User knows to run `orchard list` and `orchard install <app_id>` for any new or changed packages
