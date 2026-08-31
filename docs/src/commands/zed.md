# Zed

**Platforms:** Unix (`linux`, `darwin`, `wsl`)

Back up and restore portable [Zed user settings](https://zed.dev/docs/configuring-zed) while keeping machine-bound integrations local.

## Settings layers

- **Portable source** — `~/.config/zed/settings.shared.json`, managed by chezmoi from `home/dot_config/zed/settings.shared.json`
- **Ignored keys** — `~/.config/zed/settings.ignored.json`, a required JSON array of top-level keys that must remain machine-local
- **Live target** — `~/.config/zed/settings.json`

The ignored keys are `agent_servers`, `context_servers`, `language_models`, and `ssh_connections`. They are excluded during Pull and cannot override live values during Apply, even if they are accidentally added to `settings.shared.json`.

## `zed-settings-apply`

Merge portable settings into the live Zed settings file.

```shell
zed-settings-apply
```

The command accepts one JSONC object in the live file, including comments and trailing commas. It preserves live-only top-level keys, replaces managed top-level values completely, and writes canonical JSON atomically. Invalid encoding, invalid JSONC, symlinks, and non-regular files fail without replacing the target. Unchanged targets are not rewritten.

This command runs automatically from `chezmoi apply` on supported platforms.

## `zed-settings-pull`

Copy all non-ignored top-level settings from the live Zed file back into the tracked `settings.shared.json` source.

```shell
zed-settings-pull
zed-settings-pull --dry-run
```

Use `--dry-run` to print a unified diff without changing the source. Before adding a new machine-bound top-level setting, add its key to `settings.ignored.json`; Pull treats every other live key as portable.

[`chezmoi_add_configs`](./shell#chezmoi_add_configs) runs Pull automatically.
