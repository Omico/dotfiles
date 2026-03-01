# Orchard development guide

Orchard is a lightweight manager for macOS apps installed via DMG/ZIP/PKG, without Homebrew. The main script is a Fish executable that lists apps, installs them from direct URLs (or resolved at install time), and cleans the cache.

This document is for:

- **App package authors**: adding or editing `apps/<app_id>.fish`
- **Orchard maintainers**: modifying `home/dot_local/bin/executable_orchard`

---

## 1. Overview

- **Entrypoint**: `orchard` (Fish script at `~/.local/bin/orchard`, from chezmoi `home/dot_local/bin/executable_orchard`).
- **Config**: `$XDG_CONFIG_HOME/orchard` (default `~/.config/orchard`). App definitions live in `apps/*.fish`.
- **Cache**: `$XDG_CACHE_HOME/orchard` (default `~/.cache/orchard`). Downloaded archives and DMG mount points.
- **Platform**: macOS only (uses `hdiutil`, `ditto`, `installer`, `.app` paths).

### Commands

| Command                              | Description                                                                                      |
| ------------------------------------ | ------------------------------------------------------------------------------------------------ |
| `orchard list`                       | List all apps defined in `apps/*.fish` and whether each is installed (and version if available). |
| `orchard install <app_id> [--force]` | Download (if needed), then install the app. With `--force`, reinstall even if already installed. |
| `orchard cleanup`                    | Remove the cache directory (downloaded archives).                                                |

---

## 2. Architecture

### Script structure (`executable_orchard`)

The script is organized in sections (see the header comment):

| Section                  | Purpose                                                                                                                                                                           |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1. Initialization        | Set `_orchard_dir`, `_orchard_apps_dir`, `_orchard_cache_dir` from `XDG_*`.                                                                                                       |
| 2. Public API            | `orchard_fetch_*`, `orchard_cli_*` — no leading `_`; callable from app `.fish` files. Internal helpers (e.g. `_orchard_ensure_local_bin`) are defined **below** public functions. |
| 3. Usage and app loading | `_orchard_usage`, `_orchard_load_app`, `_orchard_installed`, `_orchard_version`.                                                                                                  |
| 4. DMG helpers           | Mount, unmount, install from mount, cache validation.                                                                                                                             |
| 5. Command: list         | Iterate `apps/*.fish`, load each app, print installed status and version.                                                                                                         |
| 6. Command: install      | Parse args, load app, resolve URL (if callback), ensure archive, install by type (dmg/zip/pkg), run after-install callback.                                                       |
| 7. Command: cleanup      | Delete cache dir.                                                                                                                                                                 |
| 8. Main entry            | Dispatch by subcommand.                                                                                                                                                           |

**Convention**: Functions whose names start with `_` are internal. They must **not** be defined above any non-`_` (public) function in the same logical section, so that "public first, internal below" is clear.

### App loading flow

1. `orchard list` or `orchard install <app_id>` loads the app via `_orchard_load_app <app_id>`.
2. `_orchard_load_app` sources `$_orchard_apps_dir/$app_id.fish` and validates required variables.
3. It sets defaults: `orchard_app_bundle_name` → `$orchard_app_display_name.app` if unset; `orchard_app_bundle_path` → `/Applications/$orchard_app_bundle_name` if unset.
4. During `orchard install`, if `orchard_resolve_download_url_callback` exists, it is run once to set `orchard_app_download_url` before download. Cache path is derived from URL hash and `orchard_app_download_type`.

### Install flow (high level)

1. Parse `install [--force] <app_id>`.
2. Load app; exit if required vars missing.
3. If already installed and not `--force`, exit.
4. If `orchard_resolve_download_url_callback` is defined, run it to set `orchard_app_download_url`.
5. Compute cache path; ensure archive (validate existing or download).
6. If app is running, try to quit it via `osascript`.
7. Run `orchard_before_install_callback` if defined.
8. Install by type: **dmg** (mount → copy .app → unmount), **zip** (extract → copy .app), **pkg** (run `installer -pkg ... -target /`).
9. Run `orchard_after_install_callback` if defined.

---

## 3. App package format (`apps/<app_id>.fish`)

Each app is a Fish script that sets global variables and optionally defines callbacks. The file name must be `<app_id>.fish`; `app_id` is lowercase, may contain hyphens.

### Required variables (set with `set -g`)

| Variable                    | Description                                                                                                                         |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `orchard_app_id`            | Same as the filename (e.g. `firefox` for `firefox.fish`).                                                                           |
| `orchard_app_display_name`  | Human-readable name (e.g. `"Firefox"`, `"Beyond Compare"`).                                                                         |
| `orchard_app_download_url`  | Direct download URL for the DMG/ZIP/PKG. Can be empty if you use `orchard_resolve_download_url_callback` to set it at install time. |
| `orchard_app_download_type` | One of `dmg`, `zip`, `pkg`.                                                                                                         |

### Optional variables

| Variable                  | Description                                                                                                                         |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `orchard_app_bundle_name` | Name of the `.app` inside the DMG/ZIP (default: `$orchard_app_display_name.app`). Set when the volume or zip uses a different name. |
| `orchard_app_bundle_path` | Full path where the app is installed (default: `/Applications/$orchard_app_bundle_name`). Override to install elsewhere.            |

### Optional callbacks (no arguments)

| Callback                                     | When it runs                                     | Purpose                                                                                                                                             |
| -------------------------------------------- | ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `orchard_resolve_download_url_callback`      | Once during `orchard install`, before download.  | Must set `orchard_app_download_url`. Use when the URL is not fixed (e.g. latest from GitHub or a download page). Return 0 on success, 1 on failure. |
| `orchard_before_install_callback`            | Once before download/install.                    | e.g. quit the app, remove old symlinks.                                                                                                             |
| `orchard_after_install_callback`             | Once after a successful install.                 | e.g. symlink CLI to PATH via `orchard_cli_wrapper` / `orchard_cli_symlink`, or open the app.                                                        |
| `orchard_resolve_installed_version_callback` | When `orchard list` needs the installed version. | Must echo the version string. If not defined, version is read from the app's `Info.plist` (CFBundleShortVersionString).                             |

Variables set by Orchard (do not set in the app file unless overriding):

- After load: `orchard_app_bundle_path` (if unset).
- During install only: `_orchard_app_download_url_hash`, `_orchard_app_archive_cache_path` (used internally).

---

## 4. Public API for app packages

These functions are part of the contract for app `.fish` files. They are defined in section 2 of `executable_orchard` so they exist when app files are sourced.

### Fetching URLs

**`orchard_fetch_github_api` _path_**

- GET `https://api.github.com/<path>` and print the response body to stdout.
- Returns 0 on HTTP 200 with non-empty body, 1 otherwise (errors to stderr).
- Example: `set -l json (orchard_fetch_github_api "repos/owner/repo/releases/latest")`

**`orchard_fetch_github_release_asset_url` _repo_ _pattern_**

- Uses the latest release; finds the first asset whose name matches the regex _pattern_ (jq `test()`).
- Prints that asset's `browser_download_url` to stdout.
- _repo_: `owner/repo`. _pattern_: e.g. `'MyApp_.*_aarch64\.dmg$'` (single quotes so `$` is literal; escape dots as `\.`).
- Returns 0 if a URL was found, 1 otherwise.

Example (pick DMG by arch):

```fish
function orchard_resolve_download_url_callback
    set -l pattern 'MyApp_.*_aarch64\.dmg$'
    test (uname -m) != arm64; and set pattern 'MyApp_.*_x64\.dmg$'
    set -g orchard_app_download_url (orchard_fetch_github_release_asset_url "owner/repo" "$pattern")
    return $status
end
```

### CLI in PATH (post-install)

Both functions ensure `/usr/local/bin` exists (creating it if needed). Call them from `orchard_after_install_callback` when the app provides a CLI you want on `PATH`.

**`orchard_cli_wrapper` _cli_name_ [_binary_name_]**

- Creates `/usr/local/bin/<cli_name>` as a small bash script that `exec`s the binary inside the app bundle.
- Binary path: `$orchard_app_bundle_path/Contents/MacOS/<binary_name>`. If _binary_name_ is omitted, it defaults to _cli_name_.
- Use when the CLI is the main executable in `Contents/MacOS/` (e.g. `firefox`, `Tailscale`).

**`orchard_cli_symlink` _cli_name_ _relative_path_**

- Creates a symlink `/usr/local/bin/<cli_name>` → `$orchard_app_bundle_path/<relative_path>`.
- _relative_path_ is inside the `.app`, e.g. `Contents/Resources/ollama`, `Contents/Resources/app/bin/code`.
- Use when the CLI is a helper binary or script inside the app (Electron apps often use `Contents/Resources/app/bin/...`).

Examples:

```fish
# Firefox: main binary is Firefox in Contents/MacOS
function orchard_after_install_callback
    orchard_cli_wrapper firefox
end

# Tailscale: binary name differs from desired command
function orchard_after_install_callback
    orchard_cli_wrapper tailscale Tailscale
end

# VS Code: CLI is in Resources
function orchard_after_install_callback
    orchard_cli_symlink code Contents/Resources/app/bin/code
end
```

---

## 5. Dependencies

- **Shell**: Fish.
- **External**: `curl`, `jq` (for GitHub API and many resolve callbacks), `hdiutil`, `ditto`, `installer`, `unzip`, `defaults` (for Info.plist). `sudo` is used for writing to `/Applications` and `/usr/local/bin`.
- **macOS**: DMG/ZIP/PKG handling and `.app` layout are macOS-specific.

---

## 6. Adding a new app

See the **orchard** skill **Quick workflow** (in `.cursor/skills/orchard/SKILL.md`) for a concise checklist.

1. Create `apps/<app_id>.fish` under the orchard config directory (e.g. `home/dot_config/orchard/apps/` in chezmoi).
2. Set the four required variables. If the download URL is not fixed, define `orchard_resolve_download_url_callback` and set `orchard_app_download_url` inside it (you can leave the initial URL empty).
3. Set `orchard_app_bundle_name` if the `.app` name inside the DMG/ZIP differs from `"<display name>.app"`.
4. Optionally define `orchard_after_install_callback` (e.g. `orchard_cli_wrapper` or `orchard_cli_symlink`) and/or `orchard_before_install_callback`, `orchard_resolve_installed_version_callback`.
5. Apply chezmoi so the file is present; run `orchard list` to confirm, then `orchard install <app_id>` to test.

**Reference**: `brew info --cask <cask_name>` often gives homepage, version, and artifact URL or structure, which helps when mapping to orchard variables.

---

## 7. Internal conventions (maintainers of `executable_orchard`)

- **Naming**: Public API for app packages has **no** leading `_` (e.g. `orchard_fetch_github_api`, `orchard_cli_wrapper`). Internal helpers use a leading `_` (e.g. `_orchard_ensure_local_bin`, `_orchard_load_app`).
- **Order**: In each section, define all public (no `_`) functions first, then internal (`_`) helpers that they use. Fish allows calling functions defined later in the file.
- **Comments**: Keep the top-of-file structure comment and section headers in sync with the code. Use English for comments and user-facing strings (see workspace rules).
- **Errors**: Use `echo "..." >&2` for error messages; return 1 for soft failures, `exit 1` when the script should stop (e.g. missing required vars).

---

## 8. Related files

- **Cursor rule for app packages**: `.cursor/rules/orchard-app-package.mdc` — detailed app package rules, examples, and "finding casks to convert" notes. Applies to `home/dot_config/orchard/apps/*.fish`.
- **Orchard config directory**: `home/dot_config/orchard/` (chezmoi); contains `apps/`.
- **Executable**: `home/dot_local/bin/executable_orchard` (installed as `orchard` under `~/.local/bin`).
- **This guide**: `.cursor/skills/orchard/references/development.md`.
