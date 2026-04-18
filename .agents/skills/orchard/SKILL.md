---
name: orchard
description: Create and maintain orchard app packages (apps/*.fish) for the macOS app manager in this chezmoi repo. Use when adding a new orchard package, editing an existing one, converting a Homebrew cask to orchard, updating download URLs or resolve callbacks, or when the user asks about orchard apps.
---

# Orchard package maintenance

Orchard is a lightweight manager for macOS apps installed via dmg/zip/pkg (no Homebrew). Packages are defined in **`home/dot_config/orchard/apps/<app_id>.fish`** and used by **`home/dot_local/bin/executable_orchard`** for `orchard list` and `orchard install <app_id>`.

**App package format** (required/optional variables, callbacks, public API, template, examples, Homebrew Cask reference): [references/app-package-format.md](references/app-package-format.md).

**Development guidelines** (standards for app packages and for editing `executable_orchard`): [references/development-guidelines.md](references/development-guidelines.md).

**Architecture, install flow, and maintainer conventions** (e.g. editing `executable_orchard`): [references/development.md](references/development.md).

---

## When to use this skill

- User asks to add, update, or maintain an orchard package
- User wants to convert a Homebrew cask to orchard
- User asks to fix or change an app in `home/dot_config/orchard/apps/`
- Editing download URL, resolve callback, or post-install steps for an orchard app

---

## Quick workflow

For **app packages** (`*.fish` under `home/dot_config/orchard/apps/`), treat **[development-guidelines — App package standards](references/development-guidelines.md#app-package-standards)** as the workflow source of truth: path and `app_id`, required/optional variables, resolve callback rules, `set -l` naming, post-install hooks, and English-only strings. Use **[app-package-format.md](references/app-package-format.md)** for templates, public API helpers (e.g. `orchard_fetch_github_release_asset_url`), and copy-paste examples.

After changes: `chezmoi apply`, then `orchard install <app_id>` (see [checklist](references/development-guidelines.md#before-committing-app-package-changes)).

For **editing `executable_orchard`**, follow **[development-guidelines — Main script standards](references/development-guidelines.md#main-script-standards)** and [development.md](references/development.md).

---

## Finding casks to convert to orchard

Only consider casks with **`auto_updates true`** (GUI apps with their own updater). See [app-package-format.md § Finding casks to convert](references/app-package-format.md) for the `comm` command and steps. For each candidate, run `brew info --cask <cask_name>` then add `home/dot_config/orchard/apps/<cask_name>.fish` using the Homebrew Cask mapping in that reference.

---

## Checklist before finishing

- [ ] [Before committing app package changes](references/development-guidelines.md#before-committing-app-package-changes) in development-guidelines (path, variables, English, `set -l` naming, resolve callback, verify install)
- [ ] Remind user to run `chezmoi apply` and optionally `orchard install <app_id>` to test
