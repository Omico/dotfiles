# Application settings

Edit the managed preferences under `app-settings/`, then run `chezmoi apply`. Separate lifecycle scripts apply Codex, Code/Cursor, and Zed settings on macOS and Linux, including WSL. Each retains priority `90` and stops on failure. Settings remain in the repository; no intermediate copies are installed.

| Applications | Source | Lifecycle script |
| --- | --- | --- |
| Codex | `app-settings/codex/settings.shared.toml` | `run_after_90-codex-settings.fish.tmpl` |
| Code and Cursor | `app-settings/vscode-based/` | `run_after_90-vscode-settings.fish.tmpl` |
| Zed | `app-settings/zed/` | `run_after_90-zed-settings.fish.tmpl` |

Live settings are not imported into the repository. `chezmoi_add_configs` only collects its other managed configuration files. To share a preference changed in an application, edit the corresponding repository source; the next Apply restores managed values.

## Code and Cursor

`shared.json` is required. Optional `code.json` and `cursor.json` override shared top-level values for each application. Ignored keys come from `ignored.json` and optional per-app `code.ignored.json` and `cursor.ignored.json`; these are JSON arrays of top-level key strings. Missing ignored files mean `[]`.

Apply combines shared and per-app values, removes ignored keys from the managed input, then merges into live settings. Managed top-level values replace existing values completely. Ignored and live-only values remain local.

Live targets are `~/Library/Application Support/{Code,Cursor}/User/settings.json` on macOS and `~/.config/{Code,Cursor}/User/settings.json` on Linux and WSL.

Both outputs are prepared before either is replaced. Invalid input leaves both live files unchanged; a later replacement failure rolls back earlier replacements. If an editor changes a replaced file before rollback, the newer file and its recovery backup are retained and reported.

## Zed

`app-settings/zed/settings.shared.json` holds portable top-level preferences. The required `settings.ignored.json` excludes machine integrations such as `agent_servers`, `context_servers`, `language_models`, and `ssh_connections`.

Apply merges managed top-level values into `~/.config/zed/settings.json`, preserving ignored and live-only values. Managed top-level values replace existing values completely.

## JSON settings validation

Code/Cursor and Zed share the private Fish helpers in `app-settings/apply.fish`. They require `iconv` and `jq >= 1.7` with literal-number preservation. Managed sources are strict JSON. Existing live files accept one JSONC object, including comments, trailing commas, and a UTF-8 BOM. Missing live files start empty; existing empty or comment-only files are invalid.

Invalid encoding, raw NUL bytes, invalid JSONC, symlinks, and non-regular inputs fail before target replacement. Writes are atomic and preserve existing file modes. Unchanged files are untouched. Snapshot checks detect live edits during preparation; retry a failed Apply to merge the latest values. These checks do not lock editors.

## Codex

`[settings]` in `app-settings/codex/settings.shared.toml` selects portable preferences applied to `$CODEX_HOME/config.toml` (default: `~/.codex/config.toml`). Each selected leaf overrides its live field; arrays replace as a unit. Empty tables own no fields. Providers, MCP configuration, credentials, project trust, unknown fields, comments, and runtime state keep their existing ownership. Plugin preferences control enablement; installation stays local.

The lifecycle script invokes `app-settings/codex/apply.py` through the existing uv wrapper, which installs uv on first use. Application shutdown is not required.

### Keep machine preferences

Use the local, untracked file `~/.config/codex-settings/settings.local.toml`:

```toml
preserve = [["model"], ["desktop", "codeFontSize"]]
```

These exact leaf paths keep their live values, including absence, and override shared updates and deletions. Each segment is a literal key, including any dots within it.

### Remove preferences

Deleting a shared assignment releases ownership and retains the live value. To delete the live field too, add its key-segment array to the shared file's top-level `remove` array:

```toml
remove = [["desktop", "codeFontSize"]]
```

Keep removal entries until all machines apply them, or indefinitely to remove future application rewrites. Conflicting assignments, overlapping paths, whole-table deletions, and table/scalar conflicts fail.

### Recovery

Changed files are backed up under `$CODEX_HOME/settings-sync-backups/` before atomic replacement. Existing file modes are preserved; new files and backups use `0600`, and the backup directory uses `0700`. Symlinked and hard-linked live files are rejected.

Backups can contain secrets and remain local until manually removed. Stop writers before restoring a backup with the original mode. Snapshot checks and the helper's lock detect concurrent helper writes but do not coordinate other applications. A changed source or live file causes Apply to fail; retry to use the latest values.
