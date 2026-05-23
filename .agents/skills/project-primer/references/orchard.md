# Orchard

Read this before changing Orchard, the local macOS app manager for dmg, zip, and pkg installs, in this chezmoi repository.

## Source Map

- **App packages**: `home/dot_config/orchard/apps/<app_id>.fish`
- **Main script**: `home/dot_local/bin/executable_orchard`
- **Completions**: `home/dot_config/fish/completions/orchard.fish`

These are chezmoi source paths. `chezmoi apply` maps them into `$HOME`:

- `home/dot_config/orchard/apps/*.fish` → `~/.config/orchard/apps/*.fish`
- `home/dot_local/bin/executable_orchard` → `~/.local/bin/orchard`
- `home/dot_config/fish/completions/orchard.fish` → `~/.config/fish/completions/orchard.fish`

## Routing

- Use the `orchard` skill for reusable package format, executable, public API, and completion rules.
- Use `orchard-migrate-brew` when converting Homebrew casks.
- Use `orchard-add-package` when adding a new package definition.
- Keep Orchard Fish files aligned with [fish](fish.md) and repository text rules in [english-only](english-only.md).

## Repository Rules

- When the `orchard` skill says `apps/<app_id>.fish`, use `home/dot_config/orchard/apps/<app_id>.fish` in this repo.
- When the `orchard` skill says the Orchard executable source, use `home/dot_local/bin/executable_orchard` in this repo.
- When the `orchard` skill says the Fish completion source, use `home/dot_config/fish/completions/orchard.fish` in this repo.
- For cask-conversion candidate checks, run commands from the repository root and compare against `home/dot_config/orchard/apps/*.fish`.

## Verification

- Run `chezmoi apply` after changing Orchard source files so the runtime paths reflect the source state.
- For package changes, run `orchard validate <app_id>` and `orchard list`.
- For install-surface changes, run `orchard install <app_id>` or `orchard install <app_id> --force` when practical.
- For executable or completion changes, run the relevant `orchard` subcommand and Fish completion checks when practical.
- If verification needs network access, sudo, or a local GUI state that was not used, say exactly what was not run.

## References

- Package variables, callbacks, public API, templates, and examples: `orchard` skill reference `references/app-package-format.md`
- Standards for app packages and the Orchard executable: `orchard` skill reference `references/development-guidelines.md`
- Architecture, install flow, and maintainer conventions: `orchard` skill reference `references/development.md`
