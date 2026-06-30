# Fish Script Structure

Use this reference when deciding where Fish code belongs or shaping functions and wrappers.

## File Roles

- **Interactive config**: keep broad shell setup in `config.fish`, and split focused startup snippets into `conf.d/*.fish` when supported by the surrounding workspace.
- **Autoloaded functions**: place reusable interactive functions in `functions/<name>.fish`, with one primary public function matching the file name.
- **Completions**: place command completions in `completions/<command>.fish` and define them with `complete -c <command> ...`.
- **Executables**: write standalone commands as normal Fish scripts with a Fish shebang and executable permissions.

## Execution Scope

- Use `status is-interactive` for code that should only run in interactive shells.
- Use `status is-login` for login-shell-only setup.
- Avoid slow, noisy, or side-effect-heavy startup code in non-interactive shells.
- Completions should compute candidates only; avoid installs, network calls, or state-changing work.

## Shebangs

- Put `#!/usr/bin/env fish` on the first line of standalone executable Fish scripts.
- Sourced config snippets do not require a shebang by Fish itself; follow the local workspace convention when one exists.
- Keep a blank line after the shebang when it improves readability.

## Function Shape

- Start public functions with `function name --description 'Short description'`.
- Close functions with `end` on its own line.
- Keep one primary public function per file when using Fish autoloaded functions.
- Put the primary public function before private helper functions, especially `__`-prefixed helpers, so the entry point appears before implementation details.
- Treat the body as a readable pipeline: validate inputs, prepare state, do the work, report the result.

## Arguments and Variables

- Read positional arguments from `$argv`, such as `set -l target $argv[1]`.
- Use `set -l` for local variables to avoid leaking globals.
- Use `set -gx` only when a value must be exported to child processes.
- Prefer descriptive variable names; avoid single-letter names in non-trivial logic.
- Provide sensible defaults when arguments are omitted, and make defaults clear in descriptions, usage text, or nearby comments.

## Command Lists

- Build external commands with many flags as list variables, then execute the list directly.
- Use `string join -- " " $cmd` only when printing a command for logs or diagnostics.
- Execute `$cmd` as a list so arguments stay correctly separated.

```fish
set -l cmd command-name --flag
set -a cmd --option $value

printf "Running %s\n" (string join -- " " $cmd) >&2
$cmd
```

## Errors and Wrappers

- Validate inputs early and `return 1` on failure.
- Check required commands with `command -q`.
- Return non-zero status codes for failures so callers can react.
- For repeated wrapper patterns, centralize shared logic in one private helper.
- Do not keep pass-through wrappers that only call another helper without adding validation, argument normalization, state changes, user-facing diagnostics, or a real ownership boundary; call the helper directly instead.
- Keep public wrapper functions thin: validate or ensure prerequisites, then forward `$argv`.

## Template

```fish
function example-command --description 'Short, action-oriented description'
  set -l target $argv[1]

  if test -z "$target"
    printf "Usage: example-command <target>\n" >&2
    return 1
  end

  if not test -e "$target"
    printf "Target '%s' does not exist.\n" "$target" >&2
    return 1
  end

  printf "Processing %s...\n" "$target"
end
```
