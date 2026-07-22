# Toolchains

Install or upgrade language runtimes and build tools from the shell.

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

## `fnm-upgrade-latest-lts`

**Platforms:** All

Install the latest Node.js LTS with `fnm`, set it as default, remove other installed versions, and enable `pnpm` through `corepack` when needed.

## `gradle-or-gradlew`

**Platforms:** All

Walk up from the current directory for an executable `gradlew` (stopping at a `.git` root). Run the wrapper when found; otherwise invoke `gradle`.

## `rustup`

**Platforms:** Unix (`linux`, `darwin`, `wsl`)

Ensure `~/.cargo/bin/rustup` exists (official install script on first use), then forward arguments to rustup.

## `update-jenv`

**Platforms:** macOS (`darwin`)

Clear `~/.jenv/versions/*`, scan `/Library/Java/JavaVirtualMachines/*.jdk`, register each JDK with jenv, and rehash.
