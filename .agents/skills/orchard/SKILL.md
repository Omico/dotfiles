---
name: orchard
description: Use when adding or maintaining Orchard app packages, editing the Orchard macOS app manager, converting Homebrew casks to Orchard packages, updating download URLs or resolve callbacks, or answering questions about Orchard apps.
---

# Orchard

Orchard is a lightweight manager for macOS apps installed via dmg, zip, or pkg archives without Homebrew. This skill owns the reusable package format, public API, and maintainer workflow.

Project-specific source paths, sync steps, and verification commands belong in the active repository's project primer. Load that primer before changing local files, then use this skill for the Orchard domain rules.

## References

- **Package format**: [references/app-package-format.md](references/app-package-format.md) for variables, callbacks, public API, templates, examples, and Homebrew Cask mapping.
- **Development guidelines**: [references/development-guidelines.md](references/development-guidelines.md) for app package standards, main script standards, completions, and checklists.
- **Architecture**: [references/development.md](references/development.md) for install flow, command behavior, dependencies, and maintainer conventions.

## When to use this skill

- User asks to add, update, or maintain an Orchard package.
- User wants to convert a Homebrew cask to Orchard.
- User asks to change an Orchard app definition.
- Editing download URLs, resolve callbacks, post-install steps, the Orchard executable, or completions.

## Quick workflow

- **App packages**: Read [development-guidelines — App package standards](references/development-guidelines.md#app-package-standards), then use [app-package-format.md](references/app-package-format.md) for templates, public API helpers such as `orchard_fetch_github_release_asset_url`, and examples.
- **Main script or completions**: Follow [development-guidelines — Main script standards](references/development-guidelines.md#main-script-standards) and [development.md](references/development.md).
- **Homebrew Cask conversions**: Use this skill's package format reference for candidate discovery and cask-to-package mapping.

## Finding casks to convert to orchard

Only consider casks with **`auto_updates true`** (GUI apps with their own updater). See [app-package-format.md — Finding casks to convert](references/app-package-format.md#finding-casks-to-convert) for the candidate command and steps. For each candidate, run `brew info --cask <cask_name>` and map the cask to an Orchard package using that reference.

## Checklist before finishing

- [ ] Use the repository primer for source paths, local sync steps, and required verification commands.
- [ ] For app packages, complete [Before committing app package changes](references/development-guidelines.md#before-committing-app-package-changes).
- [ ] For executable or public API changes, complete [Before committing changes to the Orchard executable](references/development-guidelines.md#before-committing-changes-to-the-orchard-executable).
