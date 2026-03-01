# Orchard app package format

Each package is defined in `home/dot_config/orchard/apps/<app_id>.fish`, read by `executable_orchard` for `orchard list` and `orchard install <app_id>`.

Apply this format when creating or editing app `.fish` files.

---

## File and naming

- **Path**: `home/dot_config/orchard/apps/<app_id>.fish`
- **app_id**: lowercase, may contain hyphens (e.g. `anythingllm`, `codex-app`, `chatgpt-atlas`); must match the filename prefix.

---

## Required variables (Fish set -g)

| Variable                    | Description                                                                                                              |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `orchard_app_id`            | Same as filename, e.g. `anythingllm`                                                                                     |
| `orchard_app_display_name`  | Display name, may contain spaces, e.g. `"AnythingLLM"`, `"ChatGPT Atlas"`                                                |
| `orchard_app_download_url`  | Direct download URL (dmg/zip/pkg), in double quotes. Can be empty if `orchard_resolve_download_url_callback` is defined. |
| `orchard_app_download_type` | `dmg`, `zip`, or `pkg`                                                                                                   |

---

## Optional variables (Fish set -g)

| Variable                  | Description                                                                                                        |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `orchard_app_bundle_name` | .app name inside the dmg/zip (default: `orchard_app_display_name.app`). Set when the volume uses a different name. |
| `orchard_app_bundle_path` | Install path of the .app (default: `/Applications/$orchard_app_bundle_name`). Set to install to a different path.  |

---

## Optional callbacks (no arguments)

All callback names use the `_callback` suffix. Lifecycle: `orchard_<phase>_install_callback` (`before`, `after`). Resolve: `orchard_resolve_<what>_callback`.

| Callback                                     | Description                                                                                                                                   |
| -------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `orchard_before_install_callback`            | Invoked once before download/install starts. Use for pre-install steps (e.g. close the app, remove old symlinks).                             |
| `orchard_after_install_callback`             | Invoked once after a successful `orchard install <app_id>`. Use for post-install steps (e.g. open app, symlink to PATH).                      |
| `orchard_resolve_download_url_callback`      | Called once during `orchard install` (before download). Must set `orchard_app_download_url`. Leave URL empty in the app file when using this. |
| `orchard_resolve_installed_version_callback` | Used by `orchard list` to show the installed version. Must echo the version string. Else read from Info.plist.                                |

Define in the app's `.fish` file as needed:

```fish
function orchard_before_install_callback
    # e.g. kill running app before reinstall
end

function orchard_after_install_callback
    open -a "My App"
end
```

---

## Public API

| Function                                 | Description                                                                                                                                                                                                                                                              |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `orchard_fetch_github_api`               | GET GitHub API path; prints response body to stdout. Arg: `path` (e.g. `repos/owner/repo/releases/latest`). Returns 0 on HTTP 200, 1 otherwise (writes error to stderr).                                                                                                 |
| `orchard_fetch_github_release_asset_url` | Gets the first asset in the latest release whose name matches the regex; prints its `browser_download_url`. Args: `repo` (owner/repo), `pattern` (jq `test()` regex; use single quotes so `$` is literal, escape dots as `\.`). Returns 0 and URL if found, 1 otherwise. |

**Example (resolve DMG by arch):**

```fish
function orchard_resolve_download_url_callback
    set -l pattern 'MyApp_.*_aarch64\.dmg$'
    if test (uname -m) != arm64
        set pattern 'MyApp_.*_x64\.dmg$'
    end
    set -g orchard_app_download_url (orchard_fetch_github_release_asset_url "owner/repo" "$pattern")
    return $status
end
```

---

## Template

```fish
set -g orchard_app_id <app_id>
set -g orchard_app_display_name "<display name>"
set -g orchard_app_download_url "<direct URL>"
set -g orchard_app_download_type dmg
```

---

## Examples

**Required only (DMG):**

```fish
set -g orchard_app_id anythingllm
set -g orchard_app_display_name "AnythingLLM"
set -g orchard_app_download_url "https://cdn.anythingllm.com/latest/AnythingLLMDesktop-Silicon.dmg"
set -g orchard_app_download_type dmg
```

**Redirect URL (DMG):**

```fish
set -g orchard_app_id slack
set -g orchard_app_display_name Slack
set -g orchard_app_download_url "https://slack.com/api/desktop.latestRelease?arch=universal&variant=dmg&redirect=true"
set -g orchard_app_download_type dmg
```

**When .app name must be set:**

```fish
set -g orchard_app_id myapp
set -g orchard_app_display_name "My App"
set -g orchard_app_bundle_name "MyApp Desktop.app"
set -g orchard_app_download_url "https://example.com/MyApp.dmg"
set -g orchard_app_download_type dmg
```

**Resolve URL from custom API (e.g. Antigravity uses zip + API):**

```fish
set -g orchard_app_id antigravity
set -g orchard_app_display_name Antigravity
set -g orchard_app_download_type zip

function orchard_resolve_download_url_callback
    set -l json (curl -sL "https://example.com/api/latest" 2>/dev/null)
    set -l url (echo "$json" | jq -r '.url')
    test -z "$url"; and return 1
    set -g orchard_app_download_url "$url"
    return 0
end
```

---

## Reference: Homebrew Cask

When creating a new orchard package, use **`brew info --cask <cask_name>`** as a reference. It shows homepage, version, and (when the cask is installed or cached) the artifact URL and .app name, which you can map to `orchard_app_display_name`, `orchard_app_download_url`, `orchard_app_download_type`, and `orchard_app_bundle_name` as needed.

---

## Finding casks to convert to orchard

Only consider casks with **`auto_updates true`** (typical for GUI apps that ship their own updater). Use **`brew outdated --cask --greedy-auto-updates`** to list installed such casks, then exclude those that already have an orchard package. Run from the chezmoi source root.

**Bash (run from repo root):**

```bash
# Installed casks that are outdated with --greedy-auto-updates (i.e. have auto_updates true)
# and have no corresponding apps/*.fish yet
comm -23 \
  <(brew outdated --cask -q --greedy-auto-updates 2>/dev/null | sort) \
  <(for f in home/dot_config/orchard/apps/*.fish; do [ -f "$f" ] && basename "$f" .fish; done | sort)
```

For each candidate, run **`brew info --cask <cask_name>`** to confirm it uses a direct dmg/zip/pkg URL (or a redirect), then add `home/dot_config/orchard/apps/<cask_name>.fish` using the mapping in "Reference: Homebrew Cask" above.

---

## Notes

- **URL**: Must be a direct dmg/zip/pkg link (or a page that 302-redirects to the file).
- **Resolve from HTML (no API)**: Use `curl -sL <page_url>` then parse with Fish `string match -r` to extract the download link, e.g. `set -l url (echo "$html" | string match -r 'href="(https://[^"]+\.dmg)"')[2]`; set `orchard_app_download_url` and `return 0` on success.
- **Set by Orchard (do not set in the app file unless overriding):**
  - When loading an app: `orchard_app_bundle_path` defaults to `/Applications/$orchard_app_bundle_name` if unset.
  - During `orchard install` only: `_orchard_app_download_url_hash` and `_orchard_app_archive_cache_path` (after `orchard_resolve_download_url_callback` if defined).
- **Resolve callback**: Runs only during `orchard install`, not during `orchard list`.
- After adding or editing, run `chezmoi apply` so `orchard list` sees the app; install with `orchard install <app_id>`.
