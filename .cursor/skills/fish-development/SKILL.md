---
name: fish-development
description: Guidelines and workflows for developing, testing, and maintaining fish shell scripts in this chezmoi repo. Use when editing fish scripts, adding new fish functions, or debugging fish-based tooling.
---

# Fish development

This skill explains how to work with fish shell scripts in this chezmoi repo, including files under `home/dot_config/fish/`, `home/dot_local/bin/`, and related helper scripts.

---

## When to use this skill

- A user asks to edit or create a `*.fish` script in this repo.
- A user wants to refactor, debug, or extend an existing fish function or script.
- A user is adding new CLI utilities under `home/dot_local/bin/` implemented in fish.
- A user wants to align new fish code with existing conventions in this dotfiles repo.

---

## Workspace-wide conventions for fish

- **Language**: All comments, messages, and user-facing strings in fish scripts must be in English (see workspace rule `english-only.mdc`).
- **Shebang and execution**:
  - For standalone executables in `home/dot_local/bin/`, start with `#!/usr/bin/env fish`.
  - For config snippets under `home/dot_config/fish/conf.d/`, do not include a shebang; they are sourced by fish on startup.
- **Interactive vs non-interactive**:
  - Use guards such as `if status is-interactive` or `if status is-login` for logic that should only run in interactive or login shells.
  - Avoid running slow or noisy code on every non-interactive invocation of fish.
- **Functions**:
  - Prefer `function name --description 'Short description'` for public functions.
  - Use `functions -e name` only when you explicitly need to erase a function.
  - Keep functions small and focused; extract helpers instead of building deeply nested logic.
- **Variables**:
  - Use `set -l` for local variables inside functions to avoid polluting the global scope.
  - Use `set -gx` only when a variable must be exported to child processes.
  - Prefer clear, descriptive variable names; avoid single-letter names in non-trivial logic.
- **Conditionals and flow**:
  - Use `test`/`[` or fish built-ins (`status is-interactive`, `string match`, etc.) rather than invoking external tools when possible.
  - Prefer early returns inside functions for error conditions to keep the main path readable.

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

---

## Development workflow for fish changes

- **Editing and reloading**:
  - For `conf.d` or function files, reload changes in a running shell with `source /path/to/file.fish`.
  - For executables under `home/dot_local/bin/`, open a new shell after `chezmoi apply` or re-run them directly via their full path.
- **Syntax checking and formatting**:
  - Use `fish -n /path/to/file.fish` to run a syntax check before committing.
  - Use `fish_indent -w /path/to/file.fish` to normalize formatting where appropriate.
- **chezmoi integration**:
  - Make edits in the chezmoi source tree (this repo), not in the target home directory.
  - After changes are ready, run `chezmoi apply` to propagate them into `$HOME`.
- **Debugging and error handling**:
  - Check exit statuses using `if not <command>` or `if test $status -ne 0`.
  - Print clear, English error messages to stderr using `printf` with `>&2` when appropriate.
  - For tricky logic, temporarily print intermediate values with `printf` to stderr and remove those lines once the issue is resolved.

---

## Style guidance

- **Formatting**:
  - Indent with two spaces; avoid tabs.
  - Group related `set` statements and conditionals logically.
- **Comments**:
  - Use comments to explain non-obvious decisions, assumptions, or edge cases.
  - Avoid restating what the code already clearly expresses.
- **User experience**:
  - Provide helpful `--help` output for user-facing commands, following existing patterns in this repo.
  - Prefer clear, concise messages that explain what happened and what the user can do next.

---

## Checklist before finishing fish work

- Fish script follows the English-only rule for comments and strings.
- Shebang, file location, and name match the intended usage (config vs executable vs completion).
- Functions use local variables (`set -l`) where appropriate and avoid leaking globals.
- Error handling and failure paths are tested and produce clear messages.
- Relevant scripts or config snippets were checked with `fish -n` and, where useful, formatted with `fish_indent`.
- Remind the user to run `chezmoi apply` (if needed) and test the updated command or shell session.
