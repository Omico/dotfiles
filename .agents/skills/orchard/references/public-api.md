# Orchard Package Public API

Read when using or changing GitHub URL helpers or post-install CLI integration.

These functions are part of the contract for app `.fish` files. They are defined in the Public API block of the Orchard executable so they exist when app files are sourced.

## Fetching URLs

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

## CLI in PATH (post-install)

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
