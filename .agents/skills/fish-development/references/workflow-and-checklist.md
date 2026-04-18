# Fish development workflow and checklist

This document covers the typical workflow for editing fish scripts in this repo and a checklist to use before finishing. For layout and function structure details, see `conventions-and-layout.md` and `function-guidelines.md`.

---

## Development workflow for fish changes

- **Editing and reloading**:
  - For `conf.d` or function files, reload changes in a running shell with `source /path/to/file.fish`.
  - After renaming or moving a function file, either start a new shell or run `functions -u <name>` so fish reloads it from the new location on next use.
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

## Checklist before finishing fish work

- **Language and comments**:
  - Fish script follows the English-only rule for comments and strings.
- **Location and naming**:
  - Shebang, file location, and name match the intended usage (config vs executable vs completion).
- **Function hygiene**:
  - Functions use local variables (`set -l`) where appropriate and avoid leaking globals.
- **Error handling**:
  - Error handling and failure paths are tested and produce clear messages.
- **Tooling**:
  - Relevant scripts or config snippets were checked with `fish -n` and, where useful, formatted with `fish_indent`.
- **chezmoi**:
  - Remind the user to run `chezmoi apply` (if needed) and test the updated command or shell session.
