# Fish

Read this before editing Fish files in this repository. Use the `fish-shell` skill for portable Fish idioms, formatting, syntax checks, and script design; this reference only owns local paths and repository contracts.

## Scope

- Fish config, snippets, functions, or completions under `home/dot_config/fish/`
- Fish-based executables under `home/dot_local/bin/executable_*`
- Fish helper scripts that are maintained in this source tree

If the change touches Orchard files, also read [orchard](orchard.md) and use the relevant Orchard skill.

## Contract

- Edit the chezmoi source paths, not the applied files in `$HOME`.
- Follow [english-only](english-only.md) for comments, descriptions, messages, and user-facing output.
- Start Fish files under `home/dot_config/fish/` with `#!/usr/bin/env fish`.
- Start standalone Fish executables under `home/dot_local/bin/` with `#!/usr/bin/env fish`.
- Keep the shebang in `conf.d` snippets even though Fish sources those files.
- Follow existing names: `executable_<name>` for local executables and `<command>.fish` for completions.

## Layout

- **Core config**: `home/dot_config/fish/config.fish`
- **Startup snippets**: `home/dot_config/fish/conf.d/*.fish`
- **Platform startup snippets**: `home/dot_config/fish/conf.d/<platform>/*.fish`
- **Functions**: `home/dot_config/fish/functions/**/*.fish`
- **Completions**: `home/dot_config/fish/completions/<command>.fish`
- **Executables**: `home/dot_local/bin/executable_*`
- **Repository scripts**: `scripts/*.fish`

## Platform routing

- `fish_platform` is initialized in `home/dot_config/fish/conf.d/00-platform.fish`.
- Expected values are `darwin`, `linux`, `wsl`, `msys`, and `other`.
- Prefer `fish_platform` over direct `uname` checks in Fish code.
- Treat `fish_platform` as read-only outside its initializer.
- Put platform-specific startup or function files under `conf.d/<platform>/` or `functions/<platform>/`.
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

- Use `fish-shell` guidance for formatting and syntax validation.
- Run targeted syntax checks for touched Fish files, for example:

  ```bash
  fish --no-execute home/dot_config/fish/relative/path/to/script.fish
  ```

- Run `chezmoi apply` when changes must propagate into `$HOME`.
- After applying `home/dot_local/bin/` executables, open a new shell or re-run the executable by full path.
