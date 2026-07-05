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

- Load the Orchard app manager skill (`orchard`) for reusable package format, executable, public API, and completion rules.
- Use the Homebrew cask migration skill (`orchard-migrate-brew`) when converting Homebrew casks.
- Use the Orchard add-package skill (`orchard-add-package`) when adding a new package definition.
- Keep Orchard Fish files aligned with [fish](fish.md) and repository text rules in [english-only](english-only.md).

## Repository Rules

Map paths from that skill into this chezmoi source tree:

- `apps/<app_id>.fish` → `home/dot_config/orchard/apps/<app_id>.fish`
- Orchard executable source → `home/dot_local/bin/executable_orchard`
- Fish completion source → `home/dot_config/fish/completions/orchard.fish`

For cask-conversion candidate checks, run commands from the repository root and compare against `home/dot_config/orchard/apps/*.fish`.

## Verification

- Run `chezmoi apply` after changing Orchard source files so the runtime paths reflect the source state.
- For package changes, run `orchard validate <app_id>` and `orchard list`.
- For install-surface changes, run `orchard install <app_id>` or `orchard install <app_id> --force` when practical.
- For executable or completion changes, run the relevant `orchard` subcommand and Fish completion checks when practical.
- If verification needs network access, sudo, or a local GUI state that was not used, say exactly what was not run.
