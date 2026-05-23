# Fish function guidelines and style

This document explains how to structure fish functions in this repo, and how to keep them readable and consistent. Use it together with `conventions-and-layout.md` (file locations) and `workflow-and-checklist.md` (development flow).

---

## General guidelines for fish functions

- **Where to put functions**:
  - Utility or CLI-like functions that you want available in interactive shells should live under `home/dot_config/fish/functions/` as separate `*.fish` files.
  - Keep one primary public function per file, with the file name matching the function name where practical.
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
  - Prefer fish built-in `string` for filtering and parsing text; see [string vs grep](#string-vs-grep).
- **Error handling and messaging**:
  - Print user-facing messages in English.
  - Send errors and diagnostics to stderr (`>&2`).
  - Choose `echo` vs `printf` using [echo vs printf](#echo-vs-printf) below; do not use one style for the whole repo when the other fits better.
  - Prefer clear, action-oriented messages such as “command failed for entry N” over generic failures.
  - Return non-zero status codes for failures so that callers and scripts can react appropriately.

---

## echo vs printf

In fish, neither command is universally “better”. Pick by message shape; stay consistent within a single function when practical.

| Situation | Prefer | Example |
| --- | --- | --- |
| Fixed one-line text (errors, usage, hints) | `echo` | `echo "fnm: command not found" >&2` |
| Interpolated values, counts, paths in a pattern | `printf` | `printf "fnm: failed to uninstall %s\n" $v >&2` |
| Explicit newlines or format strings | `printf` | `printf "Usage: %s <target>\n" (status function) >&2` |
| Snippets shared with POSIX `sh`/`bash` | `printf` | Same behavior across shells |

**Guidelines**

- **`echo`**: Default for short, literal stderr/stdout lines. Common in this repo (`fish-reload`, `stop-sync-gitignored`, `apm-add-skill`).
- **`printf`**: Use when the message includes `$variables` via `%s`, `%d`, etc., or when you need reliable `\n` termination. Include `\n` in the format string.
- **stderr**: Append `>&2` for errors, usage, and warnings so stdout stays clean for piping.
- **Per file**: Simple fixed errors may use `echo`; formatted errors use `printf` in the same file—no need to convert every `echo` to `printf`.

**Examples**

```fish
# Fixed error → echo
command -q fnm; or begin
    echo "fnm: command not found" >&2
    return 1
end

# Formatted error → printf
fnm uninstall $v; or printf "fnm: failed to uninstall %s\n" $v >&2

# Usage with placeholders → printf
printf "Usage: %s <target>\n" (status function) >&2
```

---

## string vs grep

In fish functions, **default to the built-in `string` subcommands** for matching, filtering, splitting, and trimming. Avoid spawning `grep`, `sed`, or `awk` when `string` (or a small fish loop) is enough.

| Task | Prefer | Avoid when equivalent |
| --- | --- | --- |
| Keep lines/items matching a pattern | `string match -r 'pattern'` | `grep -E 'pattern'` |
| Remove a prefix/suffix | `string replace`, `string trim` | `sed` one-liners |
| Split fields | `string split`, `string split0` | `awk '{print $n}'` for simple columns |
| Test whether text matches | `string match -q -r 'pattern'` | `grep -q` |
| Join list for display | `string join` | `tr`, `paste` |

**When external tools are still fine**

- The upstream CLI has no machine-readable output and you need a stable field extract (for example `fnm list` column 2)—`awk` may stay until a fish-native parser exists.
- You are intentionally sharing a pipeline with POSIX `sh`/`bash`.
- `string` would be significantly longer or less clear for a one-off complex transform—use judgment, not dogma.

**Guidelines**

- **Default**: `string match -r`, `string replace`, `string split`, `string trim`, `string length`, etc.
- **Lists**: Command substitution into `string match` filters list elements in place—good fit for `set -l items (...)`.
- **Regex**: Fish uses its own regex flavor; simple anchors (`^v`) usually match `grep -E` expectations.

**Examples**

```fish
# Filter version strings → string (not grep)
set -l installed (fnm list 2>/dev/null | awk '{print $2}' | string match -r '^v')

# Line-by-line filter in a pipeline
git status --ignored -s | string match -r '^!! .+'

# Quick test
if string match -q -r '^v[0-9]' -- $version
    ...
end
```

---

## or vs ||

In fish scripts in this repo, **default to `or` (and `and`)** for conditional command chaining—not `||` / `&&` from bash habit.

| Intent | Prefer | Avoid in new fish code |
| --- | --- | --- |
| Run next command only if previous failed | `cmd; or other` | `cmd \|\| other` |
| Run next command only if previous succeeded | `cmd; and other` | `cmd && other` |
| Failure handling with block | `cmd; or begin` … `end` | `cmd \|\| begin` … `end` |
| Early return on failure | `cmd; or return 1` | `cmd \|\| return 1` |

**Notes**

- Fish supports `||` and `&&` in recent versions, but **`or` / `and` are the native, readable form** and match the rest of this repo.
- Separate statements with `;` before `or` / `and`: `fnm use "$v"; or return 1`.
- Inside `if`, `or` / `and` are condition combinators (`if test -z "$x"; or test -z "$y"`)—not the same token as command-level `or`, but the same keyword family; still do not use `||` there.

**Examples**

```fish
command -q fnm; or begin
    echo "fnm: command not found" >&2
    return 1
end

fnm install --lts; or return 1

test -d "$path"; or continue
```

---

## Install-if-missing CLI wrappers

For commands that should **install via an upstream shell one-liner** when the binary is missing, reuse **`__ensure_binary_and_forward`** from `home/dot_config/fish/conf.d/00-core-functions.fish`. Do **not** define a second copy under `functions/`.

- **Signature (conceptual)**: `__ensure_binary_and_forward <bin_path> <short_name> <shell> <install_one_liner> $argv`
- **`shell`**: `sh` or `bash` — passed to `command $shell -c $install_one_liner` (same idea as `curl … | sh` / `curl … | bash` in a login shell).
- **Public function**: keep one primary function per file under `home/dot_config/fish/functions/` (for example `functions/unix/rustup.fish`), calling the helper and forwarding the user’s `$argv`.
- **Examples in this repo**: `home/dot_config/fish/functions/unix/rustup.fish` and `home/dot_config/fish/functions/unix/bun.fish`.

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
