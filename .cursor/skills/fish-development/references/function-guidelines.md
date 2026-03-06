# Fish function guidelines and style

This document explains how to structure fish functions in this repo, and how to keep them readable and consistent. Use it together with `conventions-and-layout.md` (file locations) and `workflow-and-checklist.md` (development flow).

---

## General guidelines for fish functions

- **Where to put functions**:
  - Utility or CLI-like functions that you want available in interactive shells should live under `home/dot_config/fish/functions/` as separate `*.fish` files.
  - Keep one primary public function per file, with the file name matching the function name where practical (for example `upgrade-agent-skills.fish` defines `upgrade-agent-skills`).
- **Function shape**:
  - Start with `function name --description 'Short description'` and close with `end` on its own line.
  - Use `set -l` for local variables, and treat the function body as a small, readable pipeline: validate inputs, do the work, print a summary.
- **Arguments and defaults**:
  - Read positional arguments from `$argv`, for example `set -l file $argv[1]`.
  - Provide sensible defaults when arguments are omitted (for example defaulting to a repo-root path), and document them in the description or comments.
  - Validate inputs early (check files exist, commands are available) and `return 1` on failure.
- **Building and running commands**:
  - When composing external commands with many flags, build them as a list variable (for example `set -l cmd npx skills add $source`) and append flags in loops.
  - Use `string join -- " " $cmd` when you need to print the command for logging, but execute it as `$cmd` so that arguments stay correctly separated.
- **Error handling and messaging**:
  - Print user-facing messages in English, send errors to stderr using `>&2` or `printf "...\n" >&2`.
  - Prefer clear, action-oriented messages such as “command failed for entry N” over generic failures.
  - Return non-zero status codes for failures so that callers and scripts can react appropriately.

---

## Example function template

```fish
function example-command --description 'Short, action-oriented description'
    # Local variables and argument parsing
    set -l target $argv[1]

    if test -z "$target"
        printf "Usage: example-command <target>\n" >&2
        return 1
    end

    # Main logic
    if not test -e "$target"
        printf "Target '%s' does not exist.\n" "$target" >&2
        return 1
    end

    # Happy path
    printf "Processing %s...\n" "$target"

    # If something fails, return a non-zero status
    # return 1
end
```

Use this template as a starting point and adapt variable names, usage text, and error handling to match the specific command.

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
