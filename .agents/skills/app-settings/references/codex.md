# Codex settings

Read for Codex Pull, checks, Apply, or source edits.

## Ownership

`app-settings/codex/settings.shared.toml` selects portable preferences under `[settings]` and optional top-level `remove`. The live target is `$CODEX_HOME/config.toml`, defaulting to `~/.codex/config.toml`. Machine overrides remain in `~/.config/codex-settings/settings.local.toml`; its `preserve` array contains exact leaf paths, including paths whose live values are absent.

MCP, providers, credentials, project trust, and runtime state retain their existing local or APM owners. Plugin enablement preferences do not install plugins.

## Pull and source edits

Codex has no bulk Pull command. Read the selected source fields and live TOML, then import only the portable preferences requested by the user into `[settings]`. Retain curated selections and the explicit `remove` policy; avoid copying the entire runtime configuration. Parse TOML with the existing native tooling rather than converting through JSON or YAML.

Each selected leaf overrides that live field on Apply; arrays replace as a unit. Deleting a shared assignment releases ownership and retains the live value. To delete the live field too, add its literal key-segment array to `remove`. Empty tables own no fields. Reject conflicting assignments, overlapping paths, whole-table removals, and table/scalar conflicts.

`preserve` overrides both updates and removals. Verify requested ownership against that local file without importing its contents into the tracked source.

## Check and Apply

```shell
codex-settings-apply --dry-run
codex-settings-apply
```

`--dry-run` validates and reports differences without writing. Without flags, the command merges selected preferences into the live file and returns `0` on success, including when already synchronized. The chezmoi hook uses this Apply command directly; application shutdown is not required.

The helper backs up changed live files, checks source/live snapshots before atomic replacement, and uses a lock for other helper invocations. Its lock does not coordinate other applications. If a file changes during Apply, report the failure and run it again. Applications can later rewrite shared fields; the next Apply restores shared values.

Changed live files are backed up under `$CODEX_HOME/settings-sync-backups/`; backups remain local and can contain secrets. The implementation is `app-settings/codex/apply.py`, invoked by the Fish wrapper with `uv run --script`.
