# Shell

Reload Fish configuration and push local config changes back into chezmoi.

## `chezmoi_add_configs`

**Platforms:** Unix (`linux`, `darwin`, `wsl`)

Add local configuration to the chezmoi source tree: format Fish with `fish_indent`, normalize permissions, forget and re-add Fish `conf.d` and `functions` (including platform scopes), and sync Ghostty and Starship config.

## `fish-reload`

**Platforms:** All

Re-source `config.fish` and every file under `conf.d/*.fish` without starting a new shell.

```shell
fish-reload [-v|--verbose]
```
