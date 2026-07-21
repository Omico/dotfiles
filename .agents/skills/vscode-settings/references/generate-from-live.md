# Generate from live settings

Read for **Pull**: regenerating managed layers from live Code/Cursor User `settings.json`.

## Command

```bash
python3 .agents/skills/vscode-settings/scripts/generate-from-live.py
python3 .agents/skills/vscode-settings/scripts/generate-from-live.py --help
python3 .agents/skills/vscode-settings/scripts/generate-from-live.py --dry-run
python3 .agents/skills/vscode-settings/scripts/generate-from-live.py --code PATH --cursor PATH --out PATH
```

Default `--out` is `<repo>/home/dot_config/vscode-settings`, resolved from the script path (cwd-safe).

## Behavior

1. Load each existing, non-symlink Code and Cursor User `settings.json` as exactly one JSONC object (line/block comments, trailing commas, UTF-8 BOM, and comment-like string content are supported by the package-local parser; empty/comment-only input and non-finite or out-of-range numbers are rejected)
2. Load ignore key sets from existing regular, non-symlink `ignored.json`, `code.ignored.json`, and `cursor.ignored.json` under `--out`; a missing file means `[]`, while an existing empty file is invalid
3. Classify remaining keys into `shared.json`, `code.json`, and `cursor.json` (per-app ignores drop only that app's side; the other app can still receive the key)
4. Prepare all three managed files as standard JSON, then replace the existing layers with rollback on replacement failure; rollback falls back to copying and preserves a recovery backup if restoration remains impossible

Ignored JSON files are **inputs only**; the script does not rewrite them. Edit ignore keys in those files directly.

Pull uses the package-local `scripts/vscode_settings_jsonc.py`. Push has a Fish-native normalizer; keep both implementations aligned with the JSONC behavior tests and strict-number rules.

**Regenerating overwrites** `shared.json`, `code.json`, and `cursor.json`. Restore curated managed edits afterward when needed (for example brace-glob simplifications).

## After generate

Finish with the package checklist in `SKILL.md`. Do not Push unless the user asked.

## Exit codes

- `0` — success (including `--dry-run`)
- `1` — operational or managed-layer write failure
- `2` — usage or missing/invalid input
