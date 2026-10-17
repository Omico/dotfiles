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
- **Templates:** Empty or whitespace-only output skips execution. Templates are evaluated before scripts run; check state created during the same apply at runtime. Include inputs that should trigger `onchange` in rendered content.

## Managed directories

Fish startup snippets and functions, Ghostty configuration, and Orchard packages use `exact_` source directories. Chezmoi removes unmanaged entries in those directories during file application, and includes those removals in `diff` and dry-run output. Nested directories that need the same policy also carry `exact_`; the policy is not recursive by itself. Keep installer-owned files such as Fish's `conf.d/apm.fish` in `.chezmoiignore.tmpl`. Other configuration directories retain their existing ownership.

## Validation

Check names, references, and dependency order. Render supported and unsupported platforms; check Fish syntax and formatting for nonempty output. Preview with `chezmoi apply --dry-run --verbose --source-path <source-file>`. A preview does not execute commands; verify changed runtime behavior separately, including retry and failure paths.
