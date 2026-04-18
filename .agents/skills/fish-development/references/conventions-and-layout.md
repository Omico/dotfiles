# Fish conventions and layout

This document describes workspace-wide conventions for fish scripts in this chezmoi repo and the typical file layout. For function-level structure and style, see `function-guidelines.md`.

---

## Workspace-wide conventions for fish

- **Language**:
  - All comments, messages, and user-facing strings in fish scripts must be in English (see workspace rule `english-only.mdc`).
- **Shebang and execution**:
  - For standalone executables in `home/dot_local/bin/`, start with `#!/usr/bin/env fish`.
  - For config snippets under `home/dot_config/fish/conf.d/`, include the same `#!/usr/bin/env fish` shebang as other fish scripts in this repo (see `fish-home-config.mdc`), even though fish does not require it when sourcing.
- **Interactive vs non-interactive**:
  - Use guards such as `if status is-interactive` or `if status is-login` for logic that should only run in interactive or login shells.
  - Avoid running slow or noisy code on every non-interactive invocation of fish.
- **Variables**:
  - Use `set -l` for local variables inside functions to avoid polluting the global scope.
  - Use `set -gx` only when a variable must be exported to child processes.
  - Prefer clear, descriptive variable names; avoid single-letter names in non-trivial logic.
- **Conditionals and flow**:
  - Use `test`/`[` or fish built-ins (`status is-interactive`, `string match`, etc.) rather than invoking external tools when possible.
  - Prefer early returns inside functions for error conditions to keep the main path readable.
- **Formatting**:
  - Use `fish_indent -w` to keep scripts consistently formatted before committing changes.

---

## File layout and typical locations

- **Core fish config**:
  - `home/dot_config/fish/config.fish`: top-level configuration for interactive shells.
  - `home/dot_config/fish/conf.d/*.fish`: small, focused startup snippets loaded automatically.
- **Completions**:
  - `home/dot_config/fish/completions/<command>.fish`: completions for custom CLIs in this repo, using `complete -c <command> ...`.
  - Completions should not perform work with side effects; they should only compute completion candidates.
- **Executable scripts**:
  - `home/dot_local/bin/executable_*`: user-facing commands; only treat scripts with a `#!/usr/bin/env fish` shebang as fish code for this skill.
  - Fish-based executables should be written as normal fish scripts with a shebang and executable bit set.

When adding a new script or completion, follow the naming patterns already used in this repo (`executable_<name>`, `<command>.fish`, etc.).
