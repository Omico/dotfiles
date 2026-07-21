---
name: vscode-settings
description: Generate and maintain home/dot_config/vscode-settings layers (shared, code, cursor, ignored) from live VS Code and Cursor User settings. Use when pulling or refreshing vsc/vscode-settings from live into the repo, generating or regenerating shared vs app layers, editing ignored keys, or pushing managed layers into live Code/Cursor settings.json. Do not use for keybindings, snippets, extensions, or unrelated Fish edits.
---

# VS Code settings

## Purpose

Maintain **`home/dot_config/vscode-settings/`** so `vscode-settings-apply` can merge managed layers into live Code/Cursor User `settings.json`.

## Intent

Classify **Pull vs Push** before routing. Do not do both in one turn unless the user asked for both.

- **Pull** — refresh managed layers from live (“update vsc config”, generate/regenerate from live, sync live → repo)
- **Push** — write managed layers into live (apply, merge into live, write back, `vscode-settings-apply`)
- Ambiguous “update settings/config” with no apply/live-target wording → **Pull**. After Pull, do not Push unless asked separately.

## Stop rule

Stop when the current route is enough. Do not change keybindings, snippets, extensions, or the Fish apply function unless the user asks for that surface.

## Routes

- **Paths, ignore shape, merge semantics, or Push**: Read [layout.md](references/layout.md).
- **Pull**: Read [generate-from-live.md](references/generate-from-live.md), then run the generate script.
- **Manual layer edits**: Follow Manual edits below (no extra reference).

## Manual edits

- **Ignore a key globally**: Add it to `ignored.json` and delete it from every managed layer.
- **Ignore a key for one app**: Add it to `<app>.ignored.json`, remove it from `shared.json` and that app's layer, and keep or move the other app's value into the other app's layer.
- **Manage a key**: Put identical values in `shared.json`, or app-only values in `code.json` / `cursor.json`.

## Checklist

```text
- [ ] Global ignores are absent from every managed layer; app ignores are absent from shared and the ignored app's layer
- [ ] Touched managed JSON files parse; live JSONC fixtures cover comments and trailing commas when parser behavior changes
- [ ] `pytest` passes from the repository root after changing Push, Pull, or parser behavior
- [ ] After Pull: curated edits restored when needed (e.g. brace globs)
- [ ] Apply ran iff Push was in scope
```
