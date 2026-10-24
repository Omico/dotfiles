# Zed settings

Read for Zed Apply or source edits.

## Ownership

`app-settings/zed/settings.shared.json` holds portable top-level values. `settings.ignored.json` is a required JSON array of machine-local top-level keys. The lifecycle script reads both directly from the repository; the live target stays at `~/.config/zed/settings.json`.

Ignored keys are removed from the shared input during Apply. Preserve the existing machine integration exclusions, including `agent_servers`, `context_servers`, `language_models`, and `ssh_connections`. Keep ignored keys out of the shared source.

## Apply

`home/run_after_90-zed-settings.fish.tmpl` sources `app-settings/apply.fish` and runs its Zed Apply helper during `chezmoi apply` on macOS and Linux, including WSL.

Apply shallowly overrides live top-level values. Live-only keys remain, and managed top-level values replace entire existing values. It parses live JSONC, prepares canonical JSON, and replaces the target atomically; unchanged files are untouched.

Inputs must be regular, non-symlink files. Shared and ignored sources are required; invalid encoding or JSONC fails before replacement. Code/Cursor and Zed share the Fish merge engine, requiring `iconv` and literal-number-preserving `jq >= 1.7`.
