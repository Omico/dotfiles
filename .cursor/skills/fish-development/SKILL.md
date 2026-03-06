---
name: fish-development
description: Guidelines and workflows for developing, testing, and maintaining fish shell scripts in this chezmoi repo. Use when editing fish scripts, adding new fish functions, or debugging fish-based tooling.
---

# Fish development

This skill explains how to work with fish shell scripts in this chezmoi repo, including files under `home/dot_config/fish/`, `home/dot_local/bin/`, and related helper scripts. It provides a quick overview here and points to focused reference documents for details.

---

## When to use this skill

- A user asks to edit or create a `*.fish` script in this repo.
- A user wants to refactor, debug, or extend an existing fish function or script.
- A user is adding new CLI utilities under `home/dot_local/bin/` implemented in fish.
- A user wants to align new fish code with existing conventions in this dotfiles repo.

---

## Quick start

- **Follow workspace rules**:
  - Keep all comments, messages, and user-facing strings in English.
  - Use the appropriate shebang and location based on whether the file is config, completion, or an executable.
- **Place functions correctly**:
  - Put reusable functions in `home/dot_config/fish/functions/` with one primary public function per file.
  - Name the file to match the main function where practical (for example `upgrade-agent-skills.fish` defines `upgrade-agent-skills`).
- **Keep functions small and robust**:
  - Use `set -l` for local variables and validate inputs early.
  - Handle errors with clear messages to stderr and non-zero exit codes.
- **Use the tooling**:
  - Run `fish -n` for syntax checks and `fish_indent` to keep formatting consistent.
  - Edit in the chezmoi source tree and run `chezmoi apply` when changes are ready.
- **Refer to the reference docs**:
  - For layout and file placement, see [conventions-and-layout.md](references/conventions-and-layout.md).
  - For function structure and style, see [function-guidelines.md](references/function-guidelines.md).
  - For a full workflow and pre-commit checks, see [workflow-and-checklist.md](references/workflow-and-checklist.md).
