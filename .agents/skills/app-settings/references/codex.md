# Codex settings

Read for Codex Pull, checks, Apply, or source edits.

## Ownership

`app-settings/codex/settings.shared.toml` selects portable preferences under `[settings]` and optional top-level `remove`. The live target is `$CODEX_HOME/config.toml`, defaulting to `~/.codex/config.toml`. Machine overrides remain in `~/.config/codex-settings/settings.local.toml`; its `preserve` array contains exact leaf paths, including paths whose live values are absent.

MCP, providers, credentials, project trust, and runtime state retain their existing local or APM owners. Plugin enablement preferences do not install plugins.

## Pull and source edits

Codex has no bulk Pull command. Read the selected source fields and live TOML, then import only the portable preferences requested by the user into `[settings]`. Retain curated selections and the explicit `remove` policy; avoid copying the entire runtime configuration. Parse TOML with the existing native tooling rather than converting through JSON or YAML.

Each selected leaf overrides that live field on offline Apply; arrays replace as a unit. Deleting a shared assignment releases ownership and retains the live value. To delete the live field too, add its literal key-segment array to `remove`. Empty tables own no fields. Reject conflicting assignments, overlapping paths, whole-table removals, and table/scalar conflicts.

`preserve` overrides both updates and removals. Verify requested ownership against that local file without importing its contents into the tracked source.

## Check and Apply

```shell
codex-settings-apply --dry-run
codex-settings-apply
```

`--dry-run` validates and reports differences without writing. Without flags, exit `0` means synchronized and exit `2` means shared fields are pending; neither writes live settings. The chezmoi hook uses this check.

A requested live write requires all Codex, ChatGPT, APM, and other configuration writers to remain stopped. While this chat is running in a configuration writer, finish source preparation and the dry run, then provide this command for a separate terminal after the user stops the writers:

```shell
codex-settings-apply --offline
```

The helper checks known processes and source/live snapshots before atomic replacement, but its lock does not coordinate other applications. Keep `--offline` out of automatic hooks and multi-app Apply loops that cannot satisfy the writer condition. Report pending fields and the remaining offline action rather than claiming Apply completed.

Changed live files are backed up under `$CODEX_HOME/settings-sync-backups/`; backups remain local and can contain secrets. The implementation is `app-settings/codex/apply.py`, invoked by the Fish wrapper with `uv run --script`.
