# Orchard

Read this before changing Orchard, the local macOS app manager for dmg, zip, and
pkg installs.

## Files

- **App packages**: `home/dot_config/orchard/apps/<app_id>.fish`
- **Main script**: `home/dot_local/bin/executable_orchard`
- **Completions**: `home/dot_config/fish/completions/orchard.fish`

These are source paths; `chezmoi apply` maps them into `$HOME`.

## Routing

- Use the `orchard` skill for package work and main-script changes.
- Use `orchard-migrate-brew` when converting Homebrew casks.
- Use `orchard-add-package` when adding a new package definition.
- Keep Orchard Fish files aligned with [fish](fish.md).

## References

- Package variables, callbacks, public API, templates, and examples: [app-package-format.md](../../orchard/references/app-package-format.md)
- Standards for app packages and `executable_orchard`: [development-guidelines.md](../../orchard/references/development-guidelines.md)
- Architecture, install flow, and maintainer conventions: [development.md](../../orchard/references/development.md)
