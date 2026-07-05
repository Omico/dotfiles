# APM

Read this before editing APM source files under `home/dot_apm/` or APM Fish helpers and commands:

- `home/dot_config/fish/conf.d/99-apm.fish`
- `home/dot_config/fish/functions/apm-add-skill.fish`
- `home/dot_config/fish/functions/apm-update.fish`

When editing those Fish files, also read [fish](fish.md).

## Source Files

- Treat `home/dot_apm/apm.base.yml` as the tracked base source.
- Treat `home/dot_apm/apm.custom.yml` as a local, ignored customization source.
- Treat `~/.apm/apm.yml` as the merged runtime config generated from the base and custom sources.
- Run `__apm-merge-source-config` (via `apm-update` or `apm-add-skill`) after changing source files so `~/.apm/apm.yml` stays in sync.
- Use `apm-add-skill <package>` for local custom dependencies and `apm-add-skill --global <package>` for tracked base dependencies.
- `apm-add-skill` finishes with `chezmoi add` on `~/.apm/apm.custom.yml` or `~/.apm/apm.base.yml`, depending on whether `--global` was used.

## Migration

- If you previously added local-only dependencies to the tracked `apm.yml`, move those entries into `apm.custom.yml` before running `apm-update`.

## Dependencies

- Keep every entry under `dependencies: apm:` sorted.
- Compare entries by the full dependency string exactly as written.
- Preserve the existing YAML structure and quoting style.
