---
name: app-settings
description: Edit managed Codex, Code/Cursor, and Zed preferences in app-settings, or maintain their automatic chezmoi Apply scripts.
---

# Application settings

Maintain the repository's top-level `app-settings/` as the source of managed preferences. Platform-gated `home/run_after_90-*-settings.fish.tmpl` scripts apply these preferences during `chezmoi apply`. Applications keep their existing live configuration paths.

## Operation and scope

- Edit requested source values directly. Live preferences are not imported into the repository.
- Finish source edits without applying live settings unless the user requested Apply.
- For Apply, use the matching chezmoi lifecycle script. Code and Cursor share one script and are applied together; a single-app request does not authorize writing the other application.
- Read-only validation does not authorize live writes.

## Routes

- **Code/Cursor**: read [vscode-based.md](references/vscode-based.md) for source ownership and merge behavior.
- **Codex**: read [codex.md](references/codex.md) for selected TOML fields and machine overrides.
- **Zed**: read [zed.md](references/zed.md) for portable settings and ignored integrations.

For a new application, identify its live target, source owner, local exclusions, and lifecycle script before adopting it.

## Boundaries

Keep credentials, machine integrations, runtime state, and local overrides in each application's designated local files. Own only the selected user settings; keybindings, snippets, extensions, installation, and project configuration require their own scope.

## Completion

- Parse touched managed files with their native format and check ignored/preserved ownership against the application route.
- For Fish merge changes, run `uv run --locked python -m unittest discover -s tests/vscode_settings` and `uv run --locked python -m unittest discover -s tests/zed_settings` from the repository root.
- For Codex merge changes, run `uv run --locked python -m unittest discover -s tests/codex_settings`.
- For lifecycle changes, run `uv run --locked python -m unittest discover -s tests/chezmoi -p test_app_settings.py`. Keep validation writes in a temporary HOME.
