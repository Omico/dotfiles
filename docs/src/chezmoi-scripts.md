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
- **Updates:** Homebrew, Node.js, Python, Rust, APT, and Snap updates return a nonzero status when an update step fails, so `chezmoi apply` reports the failure. Node.js and Snap updates are skipped when their tools are absent.
- **Templates:** Empty or whitespace-only output skips execution. Templates are evaluated before scripts run; check state created during the same apply at runtime. Include inputs that should trigger `onchange` in rendered content.

## Package installation

`home/.chezmoidata/darwin.toml` owns the macOS bootstrap formulae and initial Orchard app selection. `home/.chezmoidata/ubuntu.toml` owns the Ubuntu Noble APT list. Their `run_onchange_` scripts render these lists into commands, so changing the relevant list reruns its installer, including when reverting to a previously used list. Removing a list entry does not uninstall the package. Empty lists skip installation. The complete Homebrew environment remains in `Brewfile`; routine update scripts retain their existing behavior.

`run_onchange_after_30-python.fish.tmpl` installs uv-managed Python 3.11 and 3.13 on macOS and Linux, sets 3.13 as the default interpreter, and installs The Fuck through `uv tool install`. Each failed step stops the script; successful steps can be retried. Project test dependencies remain in `pyproject.toml` and `uv.lock`.

`run_after_90-python.fish.tmpl` runs on every apply on macOS and Linux. It updates the standalone uv binary first so its Python download metadata is current, upgrades all uv-managed Python versions to their latest available patch releases, then upgrades all uv-managed tools while retaining their interpreter and version requirements. A failed step stops the script and returns its status.

## Android Fish completions

`run_onchange_after_95-android-completions.fish.tmpl` runs on macOS and Linux during `chezmoi apply` when its rendered content changes. It includes hashes of the installed Android CLI version and the generator source. Priority `95` places generation after the `90`-series package updates and Python maintenance. If Android CLI is absent, it skips generation.

The Python standard-library generator runs through uv with the managed Python 3.13 installed by the Python setup script. It ignores the caller's Python project and disables interpreter downloads. It reads the full CLI help tree, joins wrapped descriptions, generates standard Fish completion definitions, syntax-checks them, and atomically installs `~/.config/fish/completions/android.fish`. Failures preserve the previous file. The generated file stays local through `.chezmoiignore.tmpl`; each machine uses its installed CLI. Opening a terminal and completing commands never runs Python or invokes Android CLI, including version queries.

Install or upgrade Android CLI, then run `chezmoi apply`. Changes made outside chezmoi are detected only at apply time. Templates render before scripts execute: if the same apply upgrades Android CLI after template evaluation, run apply again to detect the new version. Only chezmoi decides whether regeneration is needed; invoking the generator directly always rebuilds the file.

To rebuild a deleted or manually changed output without changing the CLI version, run:

```shell
uv run --quiet --no-project --managed-python --no-python-downloads --python 3.13 --script ~/.local/libexec/android-fish-completions.py
```

After generating, new Fish shells load the result automatically. Reload it in an existing shell with `source ~/.config/fish/completions/android.fish`.

## Managed directories

Fish startup snippets and functions, Ghostty configuration, and Orchard packages use `exact_` source directories. Chezmoi removes unmanaged entries in those directories during file application, and includes those removals in `diff` and dry-run output. Nested directories that need the same policy also carry `exact_`; the policy is not recursive by itself. Keep installer-owned files such as Fish's `conf.d/apm.fish` in `.chezmoiignore.tmpl`. Other configuration directories retain their existing ownership.

## Validation

Check names, references, and dependency order. Render supported and unsupported platforms; check Fish syntax and formatting for nonempty output. Preview with `chezmoi apply --dry-run --verbose --source-path <source-file>`. A preview does not execute commands; verify changed runtime behavior separately, including retry and failure paths.
