---
name: orchard
description: "Use for Orchard app questions, package authoring and maintenance, Homebrew cask conversions, and manager, API, or completion changes."
---

# Orchard

Orchard is a lightweight manager for macOS apps installed via dmg, zip, or pkg archives without Homebrew. This skill owns the reusable package format, public API, and maintainer workflow.

Project-specific source paths, sync steps, and verification commands belong in the active repository's project primer. Load that primer before changing local files, then use this skill for the Orchard domain rules.

## Select the references

- **Any source change**: Read [development-guidelines.md](references/development-guidelines.md) for the applicable package, executable, or completion standards and completion checklist.
- **Package fields, callbacks, or Homebrew cask conversions**: Read [app-package-format.md](references/app-package-format.md) for the contract, minimal template, candidate discovery, and cask mapping. Candidate discovery only considers casks with `auto_updates true`.
- **GitHub URL helpers or CLI integration callbacks**: Read [public-api.md](references/public-api.md) for `orchard_fetch_*`, `orchard_cli_wrapper`, and `orchard_cli_symlink`.
- **Package examples**: Read [package-examples.md](references/package-examples.md) when a fixed URL, redirect, bundle override, DMG installer, or custom API example is needed.
- **Executable or completion changes**: Read [development.md](references/development.md) for command behavior, architecture, install and validation flows, recovery, and dependencies.

Load only the references needed for the current task.

## Checklist before finishing

- [ ] Use the repository primer for source paths, local sync steps, and required verification commands.
- [ ] For app packages, complete [Before committing app package changes](references/development-guidelines.md#before-committing-app-package-changes).
- [ ] For executable or public API changes, complete [Before committing changes to the Orchard executable](references/development-guidelines.md#before-committing-changes-to-the-orchard-executable).
