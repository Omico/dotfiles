# Orchard Package Examples

Read when choosing a package shape for a fixed URL, redirect, bundle-name override, DMG installer, or custom API.

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

**When a DMG contains a PKG installer:**

```fish
set -g orchard_app_id example-suite
set -g orchard_app_display_name "Example Suite"
set -g orchard_app_bundle_name "Example.app"
set -g orchard_app_pkg_name "Example Installer.pkg"
set -g orchard_app_download_url "https://example.com/ExampleSuite.dmg"
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
