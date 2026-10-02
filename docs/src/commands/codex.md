# Codex

## `codex-settings-apply`

**Platforms:** Unix (`linux`, `darwin`, `wsl`) · **Requires:** `uv`

Sync selected preferences with `$CODEX_HOME/config.toml` (default: `~/.codex/config.toml`). Providers, MCP configuration, credentials, project trust, and runtime state stay local.

### Check and apply

```shell
codex-settings-apply --dry-run
```

This validates the merged configuration and lists changed field paths. Without flags, the command returns `0` when synchronized or `2` when changes are pending. The chezmoi hook uses this check and leaves the live file untouched.

To write changes, stop Codex, ChatGPT, Codex CLI sessions, APM, and other configuration writers. In a separate terminal, run:

```shell
codex-settings-apply --offline
```

Keep writers stopped until completion. Known running writers or failed process checks block the write, but detection cannot cover every writer or prevent one from starting. Never use `--offline` in the automatic hook.

### Share preferences

Edit `app-settings/codex/settings.shared.toml` in the chezmoi repository. The command reads this source directly; no intermediate copy is installed.

Each leaf under `[settings]` overrides that field on offline apply. Arrays replace as a unit; unknown fields and comments are preserved. Empty tables own no fields. Plugin flags control enablement; installation stays local.

To share App changes, copy the selected values into this source file. Otherwise, the next offline apply restores the shared values. `chezmoi_add_configs` does not import Codex settings.

### Keep machine preferences

Create the local, untracked file `~/.config/codex-settings/settings.local.toml`:

```toml
preserve = [["model"], ["desktop", "codeFontSize"]]
```

These exact leaf paths keep their live values, including absence, and override shared updates and deletions. Each segment is a literal key, including any dots within it.

### Remove preferences

Delete a shared assignment to release ownership and retain its live value. To delete the live field too, add its path to the shared file's top-level `remove` array:

```toml
remove = [["desktop", "codeFontSize"]]
```

Keep the entry until all machines apply it, or indefinitely to remove future App rewrites. Empty table headers may remain. Conflicting assignments, overlapping paths, whole-table deletions, and table/scalar conflicts fail.

### Recover

Changed files are backed up under `$CODEX_HOME/settings-sync-backups/` before atomic replacement. Existing file modes are preserved; new files and backups use `0600`, and the backup directory uses `0700`. Unchanged files are untouched; symlinked and hard-linked live files are rejected.

Backups can contain secrets and remain local until manually removed. Stop all writers before restoring a backup with the original file mode. Snapshot checks and the helper's lock supplement the offline requirement; they cannot coordinate writes from other applications.

### Test

From the repository root:

```shell
uv run python -m unittest discover -s tests/codex_settings
```
