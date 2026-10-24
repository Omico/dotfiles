# Shell

Reload Fish configuration and push local config changes back into chezmoi.

## `chezmoi_add_configs`

**Platforms:** Unix (`linux`, `darwin`, `wsl`)

Add local configuration to the chezmoi source tree: format Fish with `fish_indent`, normalize permissions, use native `chezmoi re-add` for managed files and `chezmoi add` for new files in Fish `conf.d` and `functions` (including platform scopes), Ghostty, and Starship. Preserve existing source attributes, including `exact_` directories and templates.

For Fish and Ghostty, forget managed non-template files that are missing locally in the selected directories only when chezmoi has a last-applied record and the current source content matches that record, so the next apply does not restore deleted files. Preserve and report source files that have never been applied or have pending content changes. Preserve templates, ignored files, and Fish files for other platform scopes. Checking last-applied file hashes requires `jq`.

## `fish-reload`

**Platforms:** All

Re-source `config.fish` and every file under `conf.d/*.fish` without starting a new shell.

```shell
fish-reload [-v|--verbose]
```
