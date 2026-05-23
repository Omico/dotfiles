# Fish Development Workflow

Use this reference when formatting, checking, reloading, or debugging Fish shell changes.

## Formatting

- Use `fish_indent` to keep Fish scripts consistently formatted.
- After changing a `.fish` file, format the touched file when practical.

```bash
fish_indent -w path/to/script.fish
```

For multiple files, restrict bulk formatting to the relevant subtree when possible:

```bash
find path/to/fish/files -name '*.fish' -print0 | xargs -0 fish_indent -w
```

## Syntax Checks

- Run a Fish syntax check on changed scripts before finishing.
- `fish -n` and `fish --no-execute` are equivalent choices; prefer whichever local tooling already uses.

```bash
fish -n path/to/script.fish
fish --no-execute path/to/script.fish
```

Batch checks are useful after broad edits:

```bash
find path/to/fish/files -name '*.fish' -print0 | xargs -0 -n1 fish --no-execute
```

## Reloading Changes

- For config snippets or functions, reload a changed file in a running shell with `source /path/to/file.fish`.
- After renaming or moving an autoloaded function file, start a new shell or run `functions -e <name>` so Fish reloads it on next use.
- For standalone executables, run the changed script directly or start a fresh shell if lookup paths or generated files changed.

## Debugging

- Check command failures with `if not <command>` or by inspecting `$status` when needed.
- Print temporary debug values to stderr so stdout remains pipeable.
- Remove temporary debug output before finishing.

## Checklist

- **Formatting**: touched `.fish` files were formatted where appropriate.
- **Syntax**: changed scripts passed `fish -n` or `fish --no-execute`.
- **Reloading**: the relevant shell session or function autoload cache was refreshed when needed.
- **Failure paths**: expected errors return non-zero status and produce clear diagnostics.
