# Fish

Read this before editing Fish files in this repository. Use the Fish shell style skill (`fish-shell`) for portable idioms, formatting, syntax checks, and script design; this reference only owns local paths and repository contracts.

## Scope

- Fish config, snippets, functions, or completions under `home/dot_config/fish/`
- Fish-based executables under `home/dot_local/bin/executable_*`
- Fish helper scripts that are maintained in this source tree

If the change touches Orchard files, read [orchard](orchard.md) for chezmoi source paths, then load the Orchard app manager skill (`orchard`) for package format and API rules.

## Contract

- Edit the chezmoi source paths, not the applied files in `$HOME`.
- Follow [english-only](english-only.md) for comments, descriptions, messages, and user-facing output.
- When creating any new script or command, choose the target path by platform scope first: platform-exclusive scripts must be Fish functions under `home/dot_config/fish/functions/<platform>/<command>.fish`, not `home/dot_local/bin/executable_*`; use `home/dot_local/bin/executable_*` only for commands that should be installed as standalone executables outside the Fish platform autoload tree.
- Start Fish files under `home/dot_config/fish/` with `#!/usr/bin/env fish`.
- Start standalone Fish executables under `home/dot_local/bin/` with `#!/usr/bin/env fish`.
- Keep the shebang in `conf.d` snippets even though Fish sources those files.
- Follow existing names: `executable_<name>` for local executables and `<command>.fish` for completions.

## Layout

- **Core config**: `home/dot_config/fish/config.fish`
- **Startup snippets**: `home/dot_config/fish/conf.d/*.fish`
- **Platform startup snippets**: `home/dot_config/fish/conf.d/<platform>/*.fish`
- **Functions**: `home/dot_config/fish/functions/<command>.fish`
- **Platform functions**: `home/dot_config/fish/functions/<platform>/<command>.fish`
- **Completions**: `home/dot_config/fish/completions/<command>.fish`
- **Executables**: `home/dot_local/bin/executable_*`
- **Repository scripts**: `scripts/*.fish`

## Function layout

- Keep autoloaded public commands as flat `functions/<command>.fish` files.
- Do not create feature- or tool-specific subdirectories under `functions/`, such as `functions/apm/`.
- The only allowed subdirectories under `functions/` are platform routers: `darwin/`, `linux/`, `unix/`, and future platform names loaded by `01-platform-autoload.fish`.
- Put shared private helpers for a feature in `conf.d/` startup snippets when they must load before autoload, or colocate them with the public command file when autoload order is sufficient.
- Prefix private helpers with `__` and keep one primary public function per autoload file.
- Before extracting a private helper, check whether it will have more than one caller. If it would be referenced only once, evaluate whether the split is necessary; prefer inlining when it only wraps a short call chain without reuse, shared setup, or a distinct responsibility boundary.

## Platform routing

- `fish_platform` is initialized in `home/dot_config/fish/conf.d/00-fish-platform.fish.tmpl` from chezmoi data (`.chezmoi.os`, `.chezmoi.kernel.osrelease`).
- Re-run `chezmoi apply` after moving Fish config to a different OS or environment (for example WSL vs native Linux); the rendered value is fixed at apply time, not detected at shell startup.
- Expected values are `darwin`, `linux`, `wsl`, `msys`, and `other`.
- Prefer `fish_platform` over direct `uname` checks in Fish code.
- Treat `fish_platform` as read-only outside its initializer.
- Put platform-specific startup or function files under `conf.d/<platform>/` or `functions/<platform>/`, following the script placement rule in Contract.
- Put shared Unix Fish files under `conf.d/unix/` or `functions/unix/`; they are loaded for `linux`, `darwin`, and `wsl`.
- If a function may run before config loading, check `set -q fish_platform` and fail fast with a clear error when it is missing.

## Installer wrappers

For wrappers that install an upstream CLI when its binary is missing, reuse `__ensure_binary_and_forward` from `home/dot_config/fish/conf.d/00-core-functions.fish`. Keep public wrappers thin and do not duplicate that helper under `functions/`.

```fish
__ensure_binary_and_forward <bin_path> <short_name> <shell> <install_one_liner> $argv
```

- Use `sh` or `bash` for `<shell>`.
- Pass installer commands as the one-liner consumed by `command $shell -c`.
- Forward `$argv` so the wrapper behaves like the installed command.
- Follow `home/dot_config/fish/functions/unix/rustup.fish` and `home/dot_config/fish/functions/unix/bun.fish` as examples.

## Workflow

- Use Fish shell style skill (`fish-shell`) guidance for formatting and syntax validation.
- Run targeted syntax checks for touched Fish files, for example:

  ```bash
  fish --no-execute home/dot_config/fish/relative/path/to/script.fish
  ```

- Run `chezmoi apply` when changes must propagate into `$HOME`.
- After applying `home/dot_local/bin/` executables, open a new shell or re-run the executable by full path.
