# Fish Language Idioms

Use this reference when editing expression-level Fish code: user-facing output, command substitutions, text/list handling, or status-based branching.

## First Principles

- **Streams are contracts**: stdout is for data a caller may pipe; stderr is for diagnostics, usage, warnings, and errors.
- **Fish values are lists**: prefer Fish built-ins that preserve list behavior before spawning text tools.
- **Command status is control flow**: write status checks in Fish's native `or` / `and` form.
- **Clarity beats blanket rewrites**: keep an external tool when it is the clearest parser for a non-trivial upstream format.

## Streams

- Send errors, usage text, and warnings to stderr with `>&2`.
- Keep user-facing strings concise and appropriate for the project.
- Use `echo` for fixed one-line messages.
- Use `printf` when formatting variable values through placeholders such as `%s` or `%d`, and include `\n` in the format string.
- Use `printf` for snippets intentionally shared with POSIX shells.

```fish
echo "tool: command not found" >&2
printf "tool: failed to process %s\n" $target >&2
printf "Usage: %s <target>\n" (status function) >&2
```

Avoid using `echo` for formatted multi-value messages, and avoid writing diagnostics to stdout.

## Data

- Default to built-in `string` for matching, filtering, splitting, trimming, replacing, and joining in `.fish` files.
- Use `string match -r` instead of `grep -E` when filtering lines or list items by pattern.
- Use `string split`, `string replace`, and `string trim` instead of `awk` or `sed` for simple field, prefix, or suffix work.

```fish
set -l fish_files (string match -r '.*\.fish$' -- $files)
set -l path_parts (string split ':' -- $PATH)

if string match -q -r '^v[0-9]' -- $app_version
  ...
end
```

Keep `awk`, `grep`, or `sed` when the upstream format has no Fish-native parser and the extraction is non-trivial. POSIX-shared snippets or scripts not written for Fish may use traditional tools.

## Status

- Default to `or` and `and`, not `||` and `&&`, when chaining commands on success or failure.
- Separate the prior command from `or` or `and` with `;`.
- Use `cmd; or begin` for failure blocks and `cmd; or return 1` for early failure exits.

```fish
build_project; or return 1
command -q tool; or begin
  echo "tool: command not found" >&2
  return 1
end

test -d "$path"; or continue
```

Avoid bash-style chaining in new Fish code:

```fish
build_project || return 1
test -d "$path" || continue
```

## Review Checklist

- **Streams**: errors, usage, and warnings go to stderr; stdout remains pipeable data.
- **Messages**: fixed lines use `echo`; formatted values use `printf` with an explicit newline.
- **Data**: simple text operations use `string`; external text tools have a clear parsing reason.
- **Status**: command chaining uses `cmd; or ...` and `cmd; and ...` rather than bash operators.
- **Names**: avoid assigning to Fish special variables such as `version`; prefer descriptive names such as `app_version`.
