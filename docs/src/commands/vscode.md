# VS Code

**Platforms:** Unix (`linux`, `darwin`, `wsl`)

Merge managed VS Code and Cursor User settings from `~/.config/vscode-settings/` into each app's live `settings.json`.

## `vscode-settings-apply`

Shallow-merge pipeline: combine shared and optional app settings with top-level replacement, drop ignored keys, then replace managed top-level values in the live settings. Ignored keys keep live values and are not created when absent.

```shell
vscode-settings-apply
```

- **Sources** — `shared.json` (required); `code.json` / `cursor.json` (optional per app)
- **Ignored keys** — `ignored.json` plus optional `code.ignored.json` / `cursor.ignored.json` (JSON string arrays of top-level keys)
- **Live format** — one JSONC object, including line comments, block comments, trailing commas, and UTF-8 BOM; a missing target starts empty, but an existing empty or comment-only file is invalid
- **Targets (macOS)** — `~/Library/Application Support/Code/User/settings.json` and `~/Library/Application Support/Cursor/User/settings.json`
- **Targets (Linux / WSL)** — `~/.config/Code/User/settings.json` and `~/.config/Cursor/User/settings.json`

Both outputs are prepared before either target is replaced, so invalid encoding or content, including raw NUL bytes, leaves the live files unchanged. If a later replacement fails, earlier replacements are rolled back. The command requires Fish, `iconv`, and `jq` 1.7 or newer with literal-number preservation; startup verifies the required `jq` behavior. Push does not invoke Python. Unchanged targets are not replaced, and comparison errors fail instead of forcing replacement.

Also runs automatically from `chezmoi apply` on Unix when the function is available (`type -q`).
