# Chezmoi script naming and priority

## Naming

Use `run_[once_|onchange_]<before|after>_<NN>-<purpose>.fish[.tmpl]`; brackets mark optional parts. Use two-digit priorities and lowercase kebab-case purposes. Include platform or release qualifiers only when needed, and enforce them in template conditions. Fish scripts start with `#!/usr/bin/env fish`; add `.tmpl` when rendering is required.

## Priority

Choose the phase first: `before` precedes file application; `after` follows it. Within the same directory and phase, lower numbers run first; equal numbers sort by purpose. Keep dependent scripts in the same directory. See [chezmoi application order](https://www.chezmoi.io/reference/application-order/).

These bands are repository conventions:

| Range | Responsibility |
| --- | --- |
| `00–09` | Cleanup and preparation |
| `10–19` | Environment and session activation |
| `20–29` | Shared system dependencies and policies |
| `30–39` | Application and service configuration |
| `40–79` | Reserved; define a responsibility before use |
| `80–89` | Setup verification |
| `90–99` | Maintenance and updates, including their result checks |

Start at the band's lowest number. Splitting a script preserves its priority: independent tasks share that number and sort by name. Change numbers only for explicit ordering dependencies, placing prerequisites before consumers. Preserve unrelated assignments. If dependencies conflict with bands, split responsibilities or document the exception beside the script.

## Execution

- **Frequency:** No condition runs on every apply; `once` runs content without a successful record; `onchange` runs new or changed rendered content. Renaming alone does not rerun successful `once` content, nor does reverting to previously successful content. See [chezmoi script behavior](https://www.chezmoi.io/user-guide/use-scripts-to-perform-actions/).
- **Recovery:** Scripts must tolerate retries and repeated execution. Consumers check required state even when prerequisite scripts are skipped.
- **Default shell:** The setup script reads the account's login shell with `dscl` on macOS or `getent` on Linux. It registers Fish in `/etc/shells` when missing and calls `chsh` only when the account uses another shell. Account lookup and shell registry failures stop setup so chezmoi can retry.
- **Updates:** Homebrew, Node.js, Python, Rust, APT, and Snap updates return a nonzero status when an update step fails, so `chezmoi apply` reports the failure. Node.js and Snap updates are skipped when their tools are absent.
- **Templates:** Empty or whitespace-only output skips execution. Templates are evaluated before scripts run; check state created during the same apply at runtime. Include inputs that should trigger `onchange` in rendered content.

## Package installation

`home/.chezmoidata/darwin.toml` owns the macOS bootstrap formulae and initial Orchard app selection. `home/.chezmoidata/ubuntu.toml` owns the Ubuntu Noble APT list. Their `run_onchange_` scripts render these lists into commands, so changing the relevant list reruns its installer, including when reverting to a previously used list. Removing a list entry does not uninstall the package. Empty lists skip installation. The complete Homebrew environment remains in `Brewfile`; routine update scripts retain their existing behavior.

`run_onchange_after_30-python.fish.tmpl` installs uv-managed Python 3.11 and 3.13 on macOS and Linux, sets 3.13 as the default interpreter, and installs The Fuck through `uv tool install`. On macOS, it also installs YubiKey Manager with uv-managed Python 3.13. Each failed step stops the script; successful steps can be retried. Project test dependencies remain in `pyproject.toml` and `uv.lock`.

`run_after_90-python.fish.tmpl` runs on every apply on macOS and Linux. It updates the standalone uv binary first so its Python download metadata is current, upgrades all uv-managed Python versions to their latest available patch releases, then upgrades all uv-managed tools while retaining their interpreter and version requirements. A failed step stops the script and returns its status.

## Application settings

`run_after_90-codex-settings.fish.tmpl`, `run_after_90-vscode-settings.fish.tmpl`, and `run_after_90-zed-settings.fish.tmpl` apply [managed application preferences](./app-settings) on macOS and Linux, including WSL. Each resolves its source files from the repository and propagates failures. Code and Cursor remain one transactional pair. The scripts run on every apply; live settings are not imported back into the repository.

## macOS configuration

The former root `macos` script is now part of `chezmoi apply`, split into three macOS-only scripts. Each uses `onchange` so unchanged successful setup does not repeat. Changing the script or its hashed helper inputs reruns that setup; manually changing a system preference does not trigger it.

- **Preferences:** `run_onchange_after_30-darwin-preferences.fish.tmpl` configures Finder, Dock, automatic updates, and mouse behavior. It closes System Settings when a graphical session is available before writing preferences. Some settings take effect after the application restarts or the user logs in again.
- **Touch ID:** `run_onchange_after_20-darwin-touch-id.fish.tmpl` enables sudo Touch ID through `/etc/pam.d/sudo_local`. An existing sufficient `pam_tid.so` rule needs no change. If other active `auth` rules exist without that rule, setup fails without changing the file: enable Touch ID manually in the intended authentication order, then run apply again. This prevents a new sufficient rule from bypassing existing required or requisite authentication checks. Otherwise, it prepends the rule while preserving the existing file; on first setup it uses Apple's `sudo_local.template`. It installs the result atomically as `root:wheel` with mode `0644`. Missing or unreadable input and failed installation stop setup. It does not keep sudo credentials alive in a background process.
- **Terminal:** `run_onchange_after_30-darwin-terminal.fish.tmpl` imports the `My` theme and selects it as the default for new windows, updating existing tabs as before. The theme and AppleScript helpers stay in the repository's `macos/` directory and are read directly through chezmoi's source directory; their hashes trigger reconfiguration when they change. Import requires a graphical login and Automation permission, may briefly open windows, and fails without recording success when no graphical session is available. Run `chezmoi apply` again after logging in. Headless maintenance can exclude scripts with `chezmoi apply --exclude=scripts`, which also excludes all other setup and update scripts.

## Android Fish completions

`run_onchange_after_95-android-completions.fish.tmpl` runs on macOS and Linux during `chezmoi apply` when its rendered content changes. It includes hashes of the installed Android CLI version and the generator source. Priority `95` places generation after the `90`-series package updates and Python maintenance. If Android CLI is absent, it skips generation.

The [`android` Fish wrapper](./commands/toolchains#android) installs the CLI on first use. Completion generation checks for an installed executable and does not trigger the wrapper's installer. After first use, apply the completion script to generate completions. To apply only the wrapper and completion script from a specific checkout, replace `/path/to/chezmoi` below with its absolute path:

```shell
chezmoi --source /path/to/chezmoi apply --source-path /path/to/chezmoi/home/dot_config/fish/exact_functions/exact_unix/android.fish.tmpl /path/to/chezmoi/home/run_onchange_after_95-android-completions.fish.tmpl
```

The generator is `scripts/android-fish-completions.py`. The update script locates it through `CHEZMOI_SOURCE_DIR` and runs it with uv-managed Python 3.13, independently of the caller's Python project and with interpreter downloads disabled. It reads the full CLI help tree, joins wrapped descriptions, syntax-checks the generated Fish definitions, and atomically installs `~/.config/fish/completions/android.fish`. Failures preserve the previous file. The generated file stays local through `.chezmoiignore.tmpl`; each machine uses its installed CLI. Opening a terminal and completing commands never runs Python or invokes Android CLI, including version queries.

Install or upgrade Android CLI, then run `chezmoi apply`. Changes made outside chezmoi are detected only at apply time. Templates render before scripts execute: if the same apply upgrades Android CLI after template evaluation, run apply again to detect the new version. Only chezmoi decides whether regeneration is needed; invoking the generator directly always rebuilds the file.

To rebuild a deleted or manually changed output without changing the CLI version, run:

```shell
uv run --quiet --no-project --managed-python --no-python-downloads --python 3.13 --script "$(chezmoi source-path)/../scripts/android-fish-completions.py"
```

After generating, new Fish shells load the result automatically. Reload it in an existing shell with `source ~/.config/fish/completions/android.fish`.

## Managed directories

Fish startup snippets and functions, Ghostty configuration, and Orchard packages use `exact_` source directories. Chezmoi removes unmanaged entries in those directories during file application, and includes those removals in `diff` and dry-run output. Nested directories that need the same policy also carry `exact_`; the policy is not recursive by itself. Keep installer-owned files such as Fish's `conf.d/apm.fish` in `.chezmoiignore.tmpl`. Other configuration directories retain their existing ownership.

## Validation

Check names, references, and dependency order. Render supported and unsupported platforms; check Fish syntax and formatting for nonempty output. Preview with `chezmoi apply --dry-run --verbose --source-path <source-file>`. A preview does not execute commands; verify changed runtime behavior separately, including retry and failure paths.
