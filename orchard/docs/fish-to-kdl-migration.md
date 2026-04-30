# Orchard KDL Migration Notes

## Purpose

This document maps the current Fish package set to the KDL schema. All current
packages are macOS packages and should migrate under `platform "macos"`.

## Current Package Coverage

The current Fish package set contains 36 packages. The proposed schema covers
all of them with declarative platform nodes.

| Pattern | Packages | Manifest support |
| --- | --- | --- |
| Fixed or redirect URL | `chatgpt-atlas`, `codex-app`, `cursor`, `discord`, `docker-desktop`, `firefox`, `github`, `google-chrome`, `iterm2`, `microsoft-auto-update`, `ollama-app`, `slack`, `steam`, `tailscale-app`, `telegram-desktop`, `visual-studio-code` | `fetch "direct"` |
| GitHub release asset | `clash-verge-rev`, `keka`, `obsidian`, `opencode-desktop`, `podman-desktop`, `rustdesk` | `fetch "github-release"` |
| JSON URL extraction | `antigravity`, `jetbrains-toolbox`, `kim`, `zed` | `request format="json"` plus `url from` |
| JSON version extraction and URL template | `gitkraken`, `parallels` | `request`, `let`, and templated `url` |
| HTML regex extraction | `beyond-compare`, `bricklink-studio`, `itermbrowserplugin`, `nomachine` | `request format="text"` plus `regex` |
| Sparkle or XML extraction | `cloudflare-warp`, `ghostty`, `wireshark-app` | `request format="sparkle"` or `format="xml"` |
| Architecture-only URL template | `unity-hub` | `let` architecture mapping plus templated `url` |

## Install Coverage

| Download and install | Packages | Support |
| --- | --- | --- |
| `download "dmg"` plus `install "copy-app"` | Most GUI app DMGs | Supported |
| `download "zip"` plus `install "copy-app"` | `antigravity`, `beyond-compare`, `github`, `gitkraken`, `iterm2`, `itermbrowserplugin` | Supported |
| `download "pkg"` plus `install "run-pkg"` | `bricklink-studio`, `cloudflare-warp`, `microsoft-auto-update`, `tailscale-app` | Supported |
| `download "dmg"` plus `install "run-pkg"` | `nomachine` | Supported with `package` |

## Post-Install Coverage

| Current behavior | Packages | Manifest support |
| --- | --- | --- |
| CLI wrapper | `firefox`, `ghostty`, `keka`, `obsidian`, `tailscale-app`, `zed` | `bin "wrapper"` |
| CLI symlink | `antigravity`, `beyond-compare`, `cursor`, `ollama-app`, `visual-studio-code` | `bin "symlink"` |
| Unhide and remove Finder xattr | `parallels` | `action "unhide"` and `action "remove-xattr"` |

## Migration Strategy

- Add Rust Orchard alongside the current Fish implementation during
  development.
- Create KDL manifests under `home/dot_config/orchard/apps`.
- Put all current package behavior under `platform "macos"`.
- Convert static direct packages first.
- Convert GitHub release packages next.
- Convert general fetch pipeline packages with fixtures for each upstream
  metadata response.
- Remove runtime Fish package loading after all current packages have KDL
  equivalents.
- Keep old Fish package files only as source-control history, not as runtime
  compatibility.

## Migration Rules

- `orchard_app_id` becomes the `app` argument.
- `orchard_app_display_name` becomes top-level `display-name`.
- `orchard_app_bundle_name` becomes `bundle` inside `platform "macos"`.
- `orchard_app_bundle_path` becomes `bundle ... path="..."`.
- `orchard_app_download_type` becomes `download`.
- `orchard_app_download_url` becomes `fetch "direct"`.
- `orchard_app_pkg_name` becomes `install "run-pkg" { package "..." }`.
- `orchard_cli_wrapper` becomes `bin "wrapper"`.
- `orchard_cli_symlink` becomes `bin "symlink"`.
- `chflags nohidden` becomes `action "unhide"`.
- `xattr -d <name>` becomes `action "remove-xattr" name="<name>"`.

Fish callbacks are not migrated as executable code. They must be translated to
declarative fetch statements, bin declarations, or explicit actions.
