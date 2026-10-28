# Toolchains

Install or upgrade language runtimes and build tools from the shell.

## `android`

**Platforms:** Unix (`linux`, `darwin`, `wsl`)

Ensure `~/.local/bin/android` exists, then forward arguments to Android CLI. Like `uv`, this wrapper uses `__ensure_binary_and_forward` and runs the [official installer](https://github.com/android/skills/blob/main/devtools/android-cli/SKILL.md#installation) only when the binary is missing. Installation supports ARM64 and x86-64. Applying the wrapper does not install or upgrade the CLI.

The installer downloads the latest CLI and initializes it. It does not pin a version or verify a published checksum. The wrapper adds `~/.local/bin` to the installer's process PATH to prevent profile edits. Existing Homebrew installations require a separate ordinary uninstall, without `--zap`. The wrapper runs no SDK install, update, or removal commands of its own.

After first use, apply the [Android completion script](../chezmoi-scripts#android-fish-completions) to generate Fish completions.

## `bun`

**Platforms:** Unix (`linux`, `darwin`, `wsl`)

Ensure `~/.bun/bin/bun` exists (official install script on first use), then forward arguments to Bun.

## `codex`

**Platforms:** Unix (`linux`, `darwin`, `wsl`)

Ensure `~/.local/bin/codex` exists (official install script on first use), then forward arguments to Codex.

## `flutter-init`

**Platforms:** Unix (`linux`, `darwin`, `wsl`)

Install or upgrade the Flutter SDK. When `flutter` is already on `PATH`, runs `flutter upgrade`. Otherwise downloads the latest release for the current OS (`darwin` → macOS, `linux`/`wsl` → Linux) and architecture (`arm64`/`x64`) from the chosen channel.

```shell
flutter-init [stable|beta|dev]
```

Default channel is `stable`.

Fresh installs extract the macOS ZIP with `unzip` and the Linux/WSL tar.xz with `tar`, then add `~/flutter/bin` to the current session's `PATH`.

Downloads use unique temporary files in `$TMPDIR` (or `/tmp` when unset or empty). If a temporary file cannot be created, installation stops before downloading to it.

## `fnm-upgrade-latest-lts`

**Platforms:** All

Install the latest Node.js LTS with `fnm`, set it as default, remove other installed versions, and enable `pnpm` through `corepack` when needed.

Stop at the first failed install, activation, removal, or Corepack setup step and return its error status to the caller.

## `gradle-or-gradlew`

**Platforms:** All

Walk up from the current directory for an executable `gradlew`, stopping at a `.git` directory or file, including worktree and submodule roots. Run the wrapper when found; otherwise invoke `gradle`.

## `mise`

**Platforms:** Unix (`linux`, `darwin`, `wsl`)

Ensure `~/.local/bin/mise` exists (official install script on first use), then forward arguments to mise. First install also activates mise in the current session. Later shells activate from `conf.d/unix` when `mise` is on `PATH`. Global `auto_update` is tracked in `~/.config/mise/config.toml`.

## `rustup`

**Platforms:** Unix (`linux`, `darwin`, `wsl`)

Ensure `~/.cargo/bin/rustup` exists (official install script on first use), then forward arguments to rustup.

## `update-jenv`

**Platforms:** macOS (`darwin`)

Clear `~/.jenv/versions/*`, scan `/Library/Java/JavaVirtualMachines/*.jdk`, register each JDK with jenv, and rehash.

If `~/.jenv` is missing, report the error and return a nonzero status without closing the calling shell.

## `uv`

**Platforms:** Unix (`linux`, `darwin`, `wsl`)

Ensure `~/.local/bin/uv` exists (official install script on first use), then forward arguments to uv.

Python development uses uv-managed interpreters (`UV_MANAGED_PYTHON=true`). On macOS and Linux, chezmoi installs Python 3.11 and 3.13, exposes 3.13 as the default `python` and `python3`, and installs The Fuck as an isolated uv tool. Homebrew continues to manage Python dependencies required by its other packages.

The Fuck uses Python 3.11 because it imports `distutils`, which is unavailable in Python 3.12 and later.

Each `chezmoi apply` on macOS and Linux updates the standalone uv binary, upgrades all uv-managed Python versions to their latest patch releases, and upgrades all installed uv tools while preserving their interpreter and version requirements. The update stops at the first failed step and reports its exit status.

Keep Python test tools in each project's development dependencies. In this repository, run `uv run --locked pytest`; do not install pytest globally.
