# Zed settings

Read for Zed Pull, Apply, or source edits.

## Ownership

`app-settings/zed/settings.shared.json` holds portable top-level values. `settings.ignored.json` is a required JSON array of machine-local top-level keys. Commands read both files directly from the repository; the live file stays at `~/.config/zed/settings.json`.

Ignored keys are excluded from Pull and removed from the shared input during Apply. Preserve the existing machine integration exclusions, including `agent_servers`, `context_servers`, `language_models`, and `ssh_connections`; add a new machine-bound key to the ignored array before Pull. Remove ignored keys from the shared source if editing it manually.

## Pull

```shell
zed-settings-pull --dry-run
zed-settings-pull
```

Dry run prints a source diff without changing the source. Pull copies every non-ignored live top-level value into the tracked shared source. Review the diff for portable ownership before accepting an import. `chezmoi_add_configs` also runs Pull.

## Apply

```shell
zed-settings-apply
```

Apply removes ignored keys from the shared input and shallowly overrides live top-level values. Live-only keys remain, and managed top-level values replace entire existing values. The command parses live JSONC, prepares canonical JSON, and replaces the target atomically; unchanged files are untouched. `chezmoi apply` runs this command on Unix.

Inputs must be regular, non-symlink files. The shared and ignored sources are required; invalid encoding or JSONC fails before replacement. Zed reuses the Fish merge engine in `vscode-settings-apply.fish`, with Fish, `iconv`, and literal-number-preserving `jq >= 1.7`.
