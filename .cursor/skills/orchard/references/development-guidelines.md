# Orchard development guidelines

Development standards for orchard (macOS app manager in this chezmoi repo). Use this doc as the **entry point** when adding or editing app packages or the main script.

---

## Document index

| Document                                       | Purpose                                                                                 |
| ---------------------------------------------- | --------------------------------------------------------------------------------------- |
| **This file**                                  | Standards, rules, and checklists for app packages and `executable_orchard`.             |
| [app-package-format.md](app-package-format.md) | Package reference: variables, callbacks, public API, template, examples, Homebrew Cask. |
| [development.md](development.md)               | Architecture, script structure, install flow, public API details, dependencies.         |

---

## Scope and roles

| Role                   | Scope                                       | Key files                                       |
| ---------------------- | ------------------------------------------- | ----------------------------------------------- |
| **App package author** | Add/edit `apps/<app_id>.fish`               | `home/dot_config/orchard/apps/*.fish`           |
| **Orchard maintainer** | Change entrypoint, public API, install flow | `home/dot_local/bin/executable_orchard`         |
| **Completions**        | Subcommand/args                             | `home/dot_config/fish/completions/orchard.fish` |

---

## App package standards

_Full variable and callback reference: [app-package-format.md](app-package-format.md)._

### File and naming

- Path: `home/dot_config/orchard/apps/<app_id>.fish`. `app_id`: lowercase, hyphens allowed; must match filename.
- All comments and user-facing strings in the `.fish` file must be in **English** (workspace rule).
- **`set -l` locals**: Use a **leading underscore** and **snake_case** (e.g. `_url`, `_version`). Avoid camelCase; prefer a clear compound name (`_website_links_base` rather than `_base`).

### Required variables

- Set: `orchard_app_id`, `orchard_app_display_name`, `orchard_app_download_url` (or resolve callback), `orchard_app_download_type` (dmg | zip | pkg).
- If using `orchard_resolve_download_url_callback`, `orchard_app_download_url` may be empty; the callback must set it and return 0 on success.

### Resolve callback contract

- **Success**: Set `orchard_app_download_url`; return 0. (Helpers may print URL to stdout.)
- **Failure**: Write error to stderr; return 1. Do not set a partial or invalid URL.
- Prefer `orchard_fetch_github_release_asset_url` for GitHub; use `orchard_fetch_github_api` + jq or curl + parse for custom APIs/HTML.
- Implement resolve callbacks (including `orchard_resolve_download_url_callback`) purely in Fish, using CLI tools like `curl`, `jq`, or `string`. Do not embed or invoke other scripting languages (e.g. Python, Ruby, Node) from app packages.

### Optional variables and callbacks

- Set `orchard_app_bundle_name` only when the `.app` inside the archive differs from `"<display name>.app"`.
- Set `orchard_app_pkg_name` when a downloaded DMG contains a `.pkg` installer instead of a directly copyable `.app`.
- CLI symlinks: `orchard_cli_wrapper` for `Contents/MacOS/<binary>`; `orchard_cli_symlink` for paths under `Contents/Resources/` or nested bins.
- Do **not** set variables orchard sets (e.g. `orchard_app_bundle_path` unless overriding; never set `_orchard_*`).

---

## Main script standards

_Script structure and section list: [development.md — Architecture](development.md#architecture)._

### Structure and naming

- Keep the top-of-file structure comment and section order in sync with the code.
- **Public API** (callable from app packages): no leading `_`; define in the Public API section of `executable_orchard`.
- **Internal**: leading `_`. In each section: define public functions first, then internal helpers (“public first, internal below”).

### Public API changes

- Document new app-callable helpers in [development.md](development.md) and, if relevant, [app-package-format.md](app-package-format.md).
- Preserve backward compatibility for existing app packages.

### Errors and platform

- Errors: `echo "message" >&2`; `return 1` for recoverable failure, `exit 1` when the script must stop.
- Comments and user-visible strings in the script must be in **English**.
- Document new external commands in [development.md — Dependencies](development.md#dependencies). Orchard is macOS-only.

---

## Completions

- Keep `home/dot_config/fish/completions/orchard.fish` in sync with subcommands and options: `list`, `install [--force] <app_id>`, `migrate brew`, `cleanup`.

---

## Converting from Homebrew Cask

- Prefer casks with **`auto_updates true`**. Steps and `comm` command: [app-package-format.md — Finding casks to convert](app-package-format.md#finding-casks-to-convert).
- Use `brew info --cask <cask_name>` and map to orchard variables as in that reference.

---

## Checklists

### Before committing app package changes

- [ ] Path is `home/dot_config/orchard/apps/<app_id>.fish` and `orchard_app_id` matches filename.
- [ ] Required variables set; if using resolve callback, URL may be empty.
- [ ] All comments and strings in the file are in English.
- [ ] `set -l` locals use a leading underscore and snake_case (e.g. `_url`).
- [ ] Resolve callback: on success set URL and return 0; on failure stderr and return 1.
- [ ] Run `chezmoi apply` and `orchard install <app_id>` (or `--force`) to verify.

### Before committing changes to `executable_orchard`

- [ ] Section order and top-of-file comment are up to date.
- [ ] Public vs internal naming; errors to stderr; English only.
- [ ] If public API or behavior changed, update [development.md](development.md) and/or [app-package-format.md](app-package-format.md).
