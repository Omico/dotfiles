---
name: orchard
description: Create and maintain orchard app packages (apps/*.fish) for the macOS app manager in this chezmoi repo. Use when adding a new orchard package, editing an existing one, converting a Homebrew cask to orchard, updating download URLs or resolve callbacks, or when the user asks about orchard apps.
---

# Orchard package maintenance

Orchard is a lightweight manager for macOS apps installed via dmg/zip/pkg (no Homebrew). Packages are defined in **`home/dot_config/orchard/apps/<app_id>.fish`** and used by **`home/dot_local/bin/executable_orchard`** for `orchard list` and `orchard install <app_id>`.

**App package format** (required/optional variables, callbacks, public API, template, examples, Homebrew Cask reference): [references/app-package-format.md](references/app-package-format.md).

**Architecture, install flow, and maintainer conventions** (e.g. editing `executable_orchard`): [references/development.md](references/development.md).

---

## When to use this skill

- User asks to add, update, or maintain an orchard package
- User wants to convert a Homebrew cask to orchard
- User asks to fix or change an app in `home/dot_config/orchard/apps/`
- Editing download URL, resolve callback, or post-install steps for an orchard app

---

## Quick workflow

### Adding a new package

1. **Choose app_id**: lowercase, hyphens allowed; must match filename `home/dot_config/orchard/apps/<app_id>.fish`.
2. **Required variables**: `orchard_app_id`, `orchard_app_display_name`, `orchard_app_download_url` (or resolve callback), `orchard_app_download_type` (dmg | zip | pkg).
3. **Optional**: `orchard_app_bundle_name` if the .app name inside the archive differs from `"<display name>.app"`.
4. **Resolve callback**: If the download URL is not static, define `orchard_resolve_download_url_callback`; leave `orchard_app_download_url` unset or empty. Use `orchard_fetch_github_release_asset_url` for GitHub releases, or curl + parse for other pages/APIs.
5. **Post-install**: Use `orchard_after_install_callback` for symlinking CLI (e.g. `orchard_cli_symlink <cli_name> Contents/MacOS/<binary>` or `orchard_cli_wrapper <cli_name>`) or other setup.
6. **Language**: All comments and strings in the .fish file must be in English (workspace rule).

After adding or editing, the user should run `chezmoi apply` then `orchard install <app_id>` to verify.

### Editing an existing package

- **URL or type change**: Update `orchard_app_download_url` and/or `orchard_app_download_type`; if using a resolve callback, update the callback logic.
- **Different .app name**: Set `orchard_app_bundle_name` to the exact name inside the dmg/zip.
- **CLI symlink**: Add or adjust `orchard_after_install_callback` with `orchard_cli_symlink` or `orchard_cli_wrapper` (see executable_orchard).

### Resolve callback patterns

- **GitHub latest release by asset name**: Use `orchard_fetch_github_release_asset_url "owner/repo" "pattern"`. Pattern is a jq `test()` regex; use single quotes, escape dots as `\.`.
- **Arch-specific DMG** (common): Set pattern to match aarch64 vs x64 based on `uname -m`, then call `orchard_fetch_github_release_asset_url`.
- **Custom API or HTML page**: Use `curl -sL` and parse with `jq` or `string match -r`; set `orchard_app_download_url` and `return 0` on success, write errors to stderr and `return 1` on failure.

---

## Finding casks to convert to orchard

Only consider casks with **`auto_updates true`** (GUI apps with their own updater). See [app-package-format.md § Finding casks to convert](references/app-package-format.md) for the `comm` command and steps. For each candidate, run `brew info --cask <cask_name>` then add `home/dot_config/orchard/apps/<cask_name>.fish` using the Homebrew Cask mapping in that reference.

---

## Checklist before finishing

- [ ] File path is `home/dot_config/orchard/apps/<app_id>.fish` and app_id matches filename
- [ ] Required variables set; if using resolve callback, URL can be empty
- [ ] All comments and user-facing strings in the .fish file are in English
- [ ] Resolve callback returns 0 on success and sets `orchard_app_download_url`; errors to stderr and return 1
- [ ] Remind user to run `chezmoi apply` and optionally `orchard install <app_id>` to test
