# Orchard Development Guidelines

Read the section for the source being changed. The project primer owns repository paths, sync steps, and local verification commands.

## App package standards

- Follow `app-package-format.md` for naming, fields, callbacks, URL requirements, and Orchard-owned variables.
- Follow repository text-language rules for comments and user-facing strings.
- Use a leading underscore and snake_case for `set -l` locals, such as `_url` and `_version`. Prefer clear compound names such as `_website_links_base` over `_base`.
- Implement resolve callbacks purely in Fish with CLI tools such as `curl`, `jq`, and `string`; app packages must not embed or invoke Python, Ruby, Node, or other scripting languages.
- For CLI integration, use `orchard_cli_wrapper` for `Contents/MacOS/<binary>` and `orchard_cli_symlink` for `Contents/Resources/` or nested binaries. Their contracts are in `public-api.md`.

## Main script standards

- Keep the top-of-file structure comment and section order synchronized with the code.
- Define app-callable public functions without a leading `_` in the executable's Public API section. Internal helpers use a leading `_`; put public functions before internal helpers in each section.
- Preserve backward compatibility for existing packages when changing public API.
- Document new app-callable helpers in `public-api.md`; update `app-package-format.md` when fields or callbacks are affected. Keep command behavior, architecture, and dependencies in `development.md`.
- Write errors with `echo "message" >&2`; return 1 for recoverable failure and exit 1 when the script must stop.
- Follow repository text-language rules for comments and user-visible strings. Orchard is macOS-only.

## Completions

Keep the project's Fish completion source synchronized with subcommands and options:

- `list`
- `validate [app_id ...]`
- `install [--force] <app_id>`
- `migrate brew`
- `cleanup`

## Converting from Homebrew Cask

Follow candidate discovery and cask mapping in `app-package-format.md`, including the `auto_updates true` filter and `brew info --cask <cask_name>` check.

## Checklists

### Before committing app package changes

- Check required fields, filename/ID match, optional bundle or installer overrides, and Orchard-owned variables against `app-package-format.md`.
- For dynamic URLs, allow an empty initial URL only with a resolver; verify that success sets a complete URL and returns 0, while failure writes to stderr and returns 1.
- Check repository text-language rules and underscore-prefixed snake_case locals.
- Follow the repository's app-directory mapping, sync steps, and Orchard verification commands.

### Before committing changes to the Orchard executable

- Check section order, structure comments, public/internal naming, error streams, and repository text-language rules.
- Update the owning API, package-format, or architecture reference when public API or behavior changes.
