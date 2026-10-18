---
name: orchard-migrate-brew
description: "Use for Homebrew-to-Orchard migration or cask package authoring, including GitHub cask lookup when local brew is unavailable."
---

# Orchard: migrate from Homebrew

Use the `orchard` skill for package format, helpers, conventions, and quality checks. Its `references/app-package-format.md` owns cask mapping. Existing package edits without migration context belong to `orchard`; unrelated shell tooling belongs to `fish-shell`.

## Boundaries

- Run `orchard migrate brew --plan` and `orchard migrate brew` in the user's real environment when Homebrew state must be accurate.
- Obtain explicit user confirmation before migration or any `brew` command that removes or modifies casks. A requested read-only plan does not authorize migration.
- Keep comments and user-visible strings in Orchard scripts in English.
- Give concise summaries; show full logs only when requested.

## Select the workflow

- An empty or very short invocation requests a global migration review, starting with a dry-run plan.
- Explicit cask names or a package-authoring request select targeted cask handling.

## Global migration

- Run `orchard migrate brew --plan` and summarize outdated casks with an existing Orchard package and those that still need one.
- If none can migrate, report that there is nothing to do and stop without a confirmation question.
- If some can migrate, ask whether to uninstall those Homebrew casks and reinstall them through Orchard, within the confirmation boundary above.
- After confirmation, run `orchard migrate brew` and summarize successes and failures.
- If the user declines, leave casks unchanged and offer to author packages for specific missing casks.

## Targeted casks and package authoring

- Parse the cask names and check `home/dot_config/exact_orchard/exact_apps/<cask>.fish` for each.
- If a package exists, explain the migration plan for that context or suggest `orchard install <app_id>` when migration is unnecessary.
- If no package exists:
  - Use `brew info --cask <cask>` when local brew is available. Otherwise, read the cask file through the GitHub API in `Homebrew/homebrew-cask`.
  - Extract the homepage, download URL, and install details; ask for missing information, including special install behavior.
  - Follow `orchard` and its package-format reference to draft and write `home/dot_config/exact_orchard/exact_apps/<cask>.fish`. The package-authoring request authorizes this source write without extra confirmation.

## Completion

- Keep plans within the requested scope and migration within the explicitly confirmed scope.
- Complete the `orchard` development-guidelines checklist for new or edited packages.
- After any package change, remind the user to run `chezmoi apply`, then `orchard list` and `orchard install <app_id>` as appropriate.
