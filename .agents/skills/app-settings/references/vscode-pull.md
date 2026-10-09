# Pull Code/Cursor settings

Read for **Pull**: regenerating managed layers from live Code/Cursor User `settings.json`.

## Scope

This command always imports both Code and Cursor and rewrites `shared.json`, `code.json`, and `cursor.json`. Both live inputs are required. `--code` and `--cursor` select input paths, not applications. For a single-app Pull request, follow Select the scope in `SKILL.md` before writing the sources. `--dry-run` only reports the paired import; it does not authorize it.

## Command

```bash
bun run --install=force scripts/pull-vscode-based.mjs
bun run --install=force scripts/pull-vscode-based.mjs --help
bun run --install=force scripts/pull-vscode-based.mjs --dry-run
bun run --install=force scripts/pull-vscode-based.mjs --code PATH --cursor PATH --out PATH
```

Run these commands from the skill directory. Requires Bun 1.3.11 or newer. Default `--out` is `<repo>/app-settings/vscode-based`, resolved from the script path (cwd-safe). When the skill is installed outside the repository, pass `--out` explicitly.

## Behavior

1. Load each existing, non-symlink Code and Cursor User `settings.json` as exactly one JSONC object (`jsonc-parser` supports line/block comments, trailing commas, UTF-8 BOM, and comment-like string content; empty/comment-only input and non-finite or out-of-range numbers are rejected)
2. Load ignore key sets from existing regular, non-symlink `ignored.json`, `code.ignored.json`, and `cursor.ignored.json` under `--out`; a missing file means `[]`, while an existing empty file is invalid
3. Classify remaining keys into `shared.json`, `code.json`, and `cursor.json` (per-app ignores drop only that app's side; the other app can still receive the key)
4. Prepare all three managed files as standard JSON, then replace the existing layers with rollback on replacement failure; rollback falls back to copying and preserves a recovery backup if restoration remains impossible

Ignored JSON files are **inputs only**; the script does not rewrite them. Edit ignore keys in those files directly.

Pull imports `jsonc-parser@3.3.1` directly. Bun downloads and caches this pinned dependency on the first run; no manifest or separate install step is needed. `--install=force` keeps inline dependency resolution active even when an ancestor has `node_modules`. Later runs use the cache. Numeric values retain their source tokens for exact integer output, and classification distinguishes integers, floats, and booleans. All parser errors are checked before writing, with source line and column numbers. Push has a Fish-native normalizer; keep both paths aligned with the JSONC behavior tests and strict-number rules.

**Regenerating overwrites** `shared.json`, `code.json`, and `cursor.json`. Restore curated managed edits afterward when needed (for example brace-glob simplifications).

## After Pull

Review the three layer diffs, restore curated edits when needed, and follow Completion in `SKILL.md`. Apply only when requested.

## Exit codes

- `0` — success (including `--dry-run`)
- `1` — operational or managed-layer write failure
- `2` — usage or missing/invalid input
