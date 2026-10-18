# Orchard Development Guide

Orchard is a lightweight manager for macOS apps installed via DMG/ZIP/PKG, without Homebrew. The main script is a Fish executable that lists apps, installs them from direct URLs (or resolved at install time), and cleans the cache.

Read when changing the Orchard executable, install or validation flow, cache handling, migration failures, or external dependencies. Package authors do not need this architecture reference.

---

## Overview

- **Entrypoint**: `orchard` (Fish script on `PATH`; source path is repository-specific).
- **Config**: `$XDG_CONFIG_HOME/orchard` (default `~/.config/orchard`). App definitions live in `apps/*.fish`.
- **Cache**: `$XDG_CACHE_HOME/orchard` (default `~/.cache/orchard`). Downloaded archives and DMG mount points.
- **Platform**: macOS only (uses `hdiutil`, `ditto`, `installer`, `.app` paths).

### Commands

| Command                              | Description                                                                                                    |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------------- |
| `orchard list`                       | List all apps defined in `apps/*.fish` and whether each is installed (and version if available).               |
| `orchard validate [app_id ...]`      | Validate all app definitions, or selected app IDs, without resolving download URLs or installing anything.     |
| `orchard install <app_id> [--force]` | Download (if needed), then install the app. With `--force`, reinstall even if already installed.               |
| `orchard migrate brew`               | Migrate outdated Homebrew casks to orchard apps where a matching app package exists; report casks without one. |
| `orchard cleanup`                    | Remove the cache directory (downloaded archives).                                                              |

---

## Architecture

### Script structure

The script is organized in sections (see the header comment):

| Section                | Purpose                                                                                                                                                                           |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Initialization         | Set `_orchard_dir`, `_orchard_apps_dir`, `_orchard_cache_dir` from `XDG_*`.                                                                                                       |
| Public API             | `orchard_fetch_*`, `orchard_cli_*` — no leading `_`; callable from app `.fish` files. Internal helpers (e.g. `_orchard_ensure_local_bin`) are defined **below** public functions. |
| Usage and app loading  | `_orchard_usage`, `_orchard_load_app`, `_orchard_installed`, `_orchard_version`.                                                                                                  |
| DMG helpers            | Mount, unmount, install from mount, cache validation.                                                                                                                             |
| Command: list          | Iterate `apps/*.fish`, load each app, print installed status and version.                                                                                                         |
| Command: validate      | Validate app package metadata and callback presence without downloading or installing apps.                                                                                       |
| Command: install       | Parse args, load app, resolve URL (if callback), ensure archive, install by type (dmg/zip/pkg), run after-install callback.                                                       |
| Command: migrate       | Implement migration flows (currently: from Homebrew casks).                                                                                                                       |
| Command: cleanup       | Delete cache dir.                                                                                                                                                                 |
| Main entry             | Dispatch by subcommand.                                                                                                                                                           |

**Convention**: Functions whose names start with `_` are internal. They must **not** be defined above any non-`_` (public) function in the same logical section, so that "public first, internal below" is clear.

### App loading flow

- **Dispatch**: `orchard list` or `orchard install <app_id>` loads the app via `_orchard_load_app <app_id>`.
- **Source and validate**: `_orchard_load_app` sources `$_orchard_apps_dir/$app_id.fish` and validates required variables, ID format, ID-to-filename match, supported download type, and URL/resolver presence.
- **Defaults**: It sets `orchard_app_bundle_name` → `$orchard_app_display_name.app` if unset; `orchard_app_bundle_path` → `/Applications/$orchard_app_bundle_name` if unset.
- **Resolve URL (install only)**: During `orchard install`, if `orchard_resolve_download_url_callback` exists, it is run once to set `orchard_app_download_url` before download. Cache path is derived from URL hash and `orchard_app_download_type`.

### Validate flow

- **Select apps**: `orchard validate` checks every `apps/*.fish`; passing app IDs checks only those packages.
- **Source package**: Each app is sourced in a cleared per-app state so callbacks and variables do not leak between packages.
- **Check metadata**: Validation checks required variables, `orchard_app_id` naming and filename match, supported download type, `orchard_app_download_url` or `orchard_resolve_download_url_callback`, and `orchard_app_pkg_name` usage.
- **No network or install**: Resolve callbacks are not executed; validation only confirms that a resolver exists when the URL is dynamic.

### Install flow (high level)

- **Parse**: `install [--force] <app_id>`.
- **Load app**: Exit if required vars missing.
- **Skip if installed**: If already installed and not `--force`, exit.
- **Resolve URL**: If `orchard_resolve_download_url_callback` is defined, run it to set `orchard_app_download_url`.
- **Archive**: Compute cache path; ensure archive (validate existing or download with `aria2c`).
- **Quit running app**: If the app is running, try to quit it via `osascript`.
- **Before-install callback**: Run `orchard_before_install_callback` if defined.
- **Install by type**: **dmg** (mount → replace `.app` or install `.pkg` from the mounted volume → unmount), **zip** (extract → replace `.app`), **pkg** (run `installer -pkg ... -target /`).
- **After-install callback**: Run `orchard_after_install_callback` if defined.

Download failures stop installation before mounting or extraction. DMG and ZIP app replacements copy into a staging directory beside the destination before moving the existing app to a backup and promoting the new bundle. Promotion failure restores the backup; if restoration also fails, Orchard retains the backup and reports its path. Successful replacement removes the backup. This recovery covers app bundle replacement, not PKG installers or callback side effects.

### Homebrew migration failures

`orchard migrate brew` returns the query error if `brew outdated` fails. During migration, it continues with other candidates after an uninstall or install failure, then returns a nonzero status if any candidate failed. Reporting packages without an Orchard definition does not clear that failure status. Migration does not restore an uninstalled cask when Orchard installation fails.

---

## Dependencies

- **Shell**: Fish.
- **External**: `aria2c` (for archive downloads), `curl`, `jq` (for GitHub API and many resolve callbacks), `hdiutil`, `ditto`, `installer`, `unzip`, `defaults` (for Info.plist), and filesystem tools including `mktemp`, `mv`, and `rm` (for staged app replacement). `sudo` is used for writing to `/Applications` and `/usr/local/bin`.
- **macOS**: DMG/ZIP/PKG handling and `.app` layout are macOS-specific.
