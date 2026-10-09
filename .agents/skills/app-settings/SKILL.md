---
name: app-settings
description: Sync or edit app-settings for Codex, VS Code/Cursor, and Zed; use for Pull from live settings, Apply to apps, or shared and local setting ownership.
compatibility: Code/Cursor Pull requires Bun 1.3.11 or newer; the first run needs npm registry access to cache its pinned inline dependency.
---

# Application settings

Maintain the repository's top-level `app-settings/`. Commands read these sources directly from `~/.local/share/chezmoi/app-settings/`; applications keep their existing live configuration paths.

## Select the operation

- **Pull**: import live preferences into repository sources. An ambiguous “update settings/config” request defaults to Pull.
- **Apply**: merge repository preferences into live settings. A dry run or status check only reports differences.
- **Edit**: change selected source values or ignored/preserved fields without importing unrelated live preferences.
- For “sync” without a direction, resolve the direction before changing files. Keep Pull and Apply separate unless the user explicitly requests both.

## Select the scope

Select the requested applications and operation before writing. “All app-settings” selects all current application directories; each retains its own import and write contract.

- **Pull or Apply for Code/Cursor**: the existing write commands operate on both applications. Pull reads both live files and rewrites three managed layers; Apply processes both live files. A Code-only or Cursor-only request requires authorization for the pair before either write. Explain the affected files and clarify that scope; if the user retains the single-app scope, stop without writing. Read-only checks do not expand write authorization.
- **Edit for Code/Cursor**: edit the requested application's source settings directly. Follow [source ownership](references/vscode-based.md#source-edits) to preserve the other application's effective settings when changing shared layers. Complete source-only edits within that ownership; live Apply requires its own scope.
- **Other applications**: follow their own routes. A request for one application does not authorize applying another.

## Routes

- **Code/Cursor Pull**: read [vscode-pull.md](references/vscode-pull.md), then run `bun run --install=force scripts/pull-vscode-based.mjs` from this skill directory.
- **Code/Cursor Apply or source edits**: read [vscode-based.md](references/vscode-based.md).
- **Codex Pull, checks, Apply, or source edits**: read [codex.md](references/codex.md).
- **Zed Pull, Apply, or source edits**: read [zed.md](references/zed.md).

For a new directory under `app-settings/`, identify its live target, source owner, local exclusions, and existing import/write command before synchronizing it. Add its route when adopting support; JSON layout alone does not establish merge semantics.

## Boundaries

Keep credentials, machine integrations, runtime state, and local overrides in each application's designated local files. Own only user settings selected by the application route; keybindings, snippets, extensions, installation, and project configuration require their own scope. Change command implementations only when requested.

## Completion

- Parse touched managed files with their native format and check ignored/preserved ownership against the application route.
- After Pull, review the source diff and retain curated edits where needed. After Edit, finish without applying live settings unless Apply was requested.
- For Apply, use the application's existing command and report its result. Codex Apply writes selected shared fields directly; its dry run only reports differences.
- If parser, Pull command, or merge behavior changes, run the affected existing tests from the repository root with `uv run --locked python -m unittest discover -s tests/vscode_settings` or `-s tests/codex_settings`. For Code/Cursor Pull changes, also run `node --test tests/vscode_settings/test_pull.test.mjs` (requires Node.js 22 or newer). For Zed command changes, verify Pull and Apply in a temporary HOME.
