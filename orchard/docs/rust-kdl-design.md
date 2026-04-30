# Orchard Rust and KDL Design

## Purpose

This document proposes a Rust rewrite of Orchard with a new KDL package
manifest format. Orchard remains a lightweight macOS application manager for
apps distributed as DMG, ZIP, or PKG files. The rewrite keeps the current user
workflow small while making package definitions declarative, strongly
validated, and easier to migrate away from executable Fish callbacks.

## Goals

- Keep one package file per app.
- Replace executable package definitions with declarative KDL manifests.
- Preserve the current command surface: `list`, `validate`, `install`,
  `migrate brew`, and `cleanup`.
- Split package behavior into clear pipeline stages: `fetch`, `download`,
  and `install`.
- Cover all current Orchard packages without package-level scripts or
  callbacks.
- Make `orchard validate` able to catch schema, selector, architecture, and
  installation metadata issues before install time.
- Keep macOS-specific operations isolated behind a small Rust interface so
  fetch and manifest logic can be tested without touching the host system.

## Non-Goals

- Orchard will not become a general package manager.
- KDL manifests will not support shell snippets, arbitrary commands, or plugin
  code.
- The first Rust version does not need parallel installs, background services,
  or a graphical UI.
- The manifest format should not try to mirror Homebrew Cask syntax.

## Design Summary

Each app is described by a KDL file under:

```text
home/dot_config/orchard/apps/<app_id>.kdl
```

The top-level manifest describes app identity, where the final download URL
comes from, what kind of file is downloaded, how that file is installed, and
which post-install side effects are needed.

```kdl
app "firefox" schema=1 {
  display-name "Firefox"
  bundle "Firefox.app"

  fetch "direct" {
    url "https://download.mozilla.org/?product=firefox-latest-ssl&os=osx"
  }

  download "dmg"
  install "copy-app"

  bin "wrapper" name="firefox"
}
```

The mental model is:

- **`fetch`** resolves the final download URL and optional release metadata.
- **`download`** describes the downloaded file format and cache validation.
- **`install`** describes the installation operation.
- **`bundle`** describes the installed app identity when an app bundle exists.
- **`bin`** and **`action`** describe allowed post-install side effects.

## Manifest Structure

### App Identity

```kdl
app "visual-studio-code" schema=1 {
  display-name "Visual Studio Code"
  bundle "Visual Studio Code.app"
}
```

- `app` argument: package ID. It must match the file name.
- `schema`: manifest schema version.
- `display-name`: human-facing name used in output and app quit requests.
- `bundle`: installed `.app` bundle name. The default path is
  `/Applications/<bundle>`.

The `bundle` node may override the installed path:

```kdl
bundle "Microsoft AutoUpdate.app" path="/Library/Application Support/Microsoft/MAU2.0/Microsoft AutoUpdate.app"
```

The `bundle` node also controls the default quit behavior before reinstalling:

```kdl
bundle "Firefox.app" quit=true
```

When `quit` is omitted and a bundle exists, Orchard should default to the
current behavior: ask the running app to quit before replacing it.

For packages that do not install a durable app bundle, Orchard should support
an explicit installed-state node:

```kdl
installed "pkg-receipt" id="com.example.pkg"
```

The `installed` node is optional. When omitted, Orchard uses `bundle` for
installed-state and version checks.

### Fetch

The `fetch` stage resolves a final download URL. It may also expose variables
such as a release version for cache names and display.

Simple fixed or redirecting URL:

```kdl
fetch "direct" {
  url "https://slack.com/api/desktop.latestRelease?arch=universal&variant=dmg&redirect=true"
}
```

GitHub latest release asset:

```kdl
fetch "github-release" repo="clash-verge-rev/clash-verge-rev" {
  asset arch="arm64" regex="Clash\\.Verge_.*_aarch64\\.dmg$"
  asset arch="x86_64" regex="Clash\\.Verge_.*_x64\\.dmg$"
}
```

General fetch pipeline:

```kdl
fetch {
  let "arch" arm64="aarch64" x86_64="x86_64"

  request "release" format="json" {
    url "https://zed.dev/api/releases/latest?asset=Zed.dmg&stable=1&os=macos&arch={arch}"
  }

  url from="release" json=".url"
}
```

The general form exists because several current packages need a small
declarative pipeline: request metadata, extract a value, then either use it as
the URL or interpolate it into a URL template.

### Fetch Statements

The general `fetch` block supports these statements:

- **`let` with architecture mapping**: maps the host architecture to a manifest
  variable.
- **`request`**: downloads metadata as `json`, `text`, `xml`, or `sparkle`.
- **`let` from request**: extracts a variable from a named request.
- **`url` literal**: sets the final URL from a template.
- **`url from`**: extracts the final URL from a named request.
- **`version`**: optionally extracts a version string for list output and cache
  metadata.

Examples:

```kdl
fetch {
  let "download_arch" arm64="arm64" x86_64="x64"
  let "livecheck_arch" arm64="-arm64" x86_64=""

  request "release" format="json" {
    url "https://release.gitkraken.com/darwin{livecheck_arch}/RELEASES"
  }

  let "version" from="release" json=".name"

  url "https://api.gitkraken.dev/releases/production/darwin/{download_arch}/{version}/GitKraken-v{version}.zip"
}
```

```kdl
fetch {
  request "page" format="text" {
    url "https://www.bricklink.com/v3/studio/download.page"
  }

  let "version" from="page" regex="\"strVersion\"\\s*:\\s*\"([^\"]+)\""

  url "https://studio.download.bricklink.info/Studio2.0/Archive/{version}/Studio+2.0.pkg"
}
```

```kdl
fetch {
  request "index" format="json" {
    url "https://download.parallels.com/website_links/desktop/index.json"
  }

  let "major_version" from="index" json-key="max-numeric"

  url "https://link.parallels.com/pdfm/v{major_version}/dmg-download"
}
```

```kdl
fetch {
  request "appcast" format="xml" {
    url "https://www.wireshark.org/update/0/Wireshark/0.0.0/macOS/arm64/en-US/stable.xml"
  }

  let "version" from="appcast" xml-text="//*[local-name()='shortVersionString']"

  url "https://www.wireshark.org/download/osx/all-versions/Wireshark%20{version}.dmg"
}
```

```kdl
fetch {
  request "appcast" format="sparkle" {
    url "https://release.files.ghostty.org/appcast.xml"
  }

  url from="appcast" sparkle-enclosure-contains="Ghostty.dmg"
}
```

### Selector Semantics

Selectors must be deliberately limited. They are part of the package schema,
not an embedded programming language.

- `json`: a jq-lite path expression over objects and arrays.
- `json-key`: object-key selection helpers, starting with `max-numeric` for
  feeds whose latest version is encoded as the largest object key.
- `regex`: a regular expression over text; the first capture group is used.
- `sparkle-enclosure-contains`: selects the last Sparkle enclosure URL whose
  URL contains the given substring.
- `xml-text`: a narrow XPath-like selector that returns normalized text.

If an extraction yields no value, more than one ambiguous value, or an invalid
URL, validation should fail with an error pointing to the manifest field.

### Template Variables

Templates may reference:

- Host variables exposed by Orchard, such as `{host.arch}`.
- Variables created by `let`, such as `{arch}` or `{version}`.
- Package identity variables, such as `{app.id}` and `{app.display_name}`.

Templates must not execute code. Missing variables are validation errors.

### Download

The `download` node describes the cached file format.

```kdl
download "dmg"
```

Supported formats:

- `dmg`: validate with DMG image checks and mount tests.
- `zip`: validate with ZIP archive checks.
- `pkg`: validate with macOS package signature or package metadata checks.

The cache key should default to a stable hash of the resolved final URL and the
download format.

### Install

The `install` node describes what Orchard does with the downloaded file.

```kdl
download "dmg"
install "copy-app"
```

```kdl
download "zip"
install "copy-app"
```

```kdl
download "pkg"
install "run-pkg"
```

```kdl
download "dmg"
install "run-pkg" {
  package "NoMachine.pkg"
}
```

Supported install operations:

- `copy-app`: find the configured app bundle inside a mounted DMG or extracted
  ZIP, then copy it to the configured bundle path.
- `run-pkg`: run the macOS installer for a downloaded PKG, or for a named PKG
  found inside a mounted DMG.

The names are intentionally action-oriented. `download "pkg"` describes the
file format, while `install "run-pkg"` describes the operation.

### Post-Install Side Effects

Only declared side effects are allowed.

CLI wrapper:

```kdl
bin "wrapper" name="zed" binary="cli"
```

Wrapper with fixed arguments:

```kdl
bin "wrapper" name="keka" binary="Keka" {
  arg "--cli"
}
```

CLI symlink:

```kdl
bin "symlink" name="code" target="Contents/Resources/app/bin/code"
```

Other allowed actions:

```kdl
action "unhide"
action "remove-xattr" name="com.apple.FinderInfo"
action "open"
```

The first schema version only needs the actions represented by current
packages. New actions should be added as explicit Rust enum variants with
validation and tests.

## Current Package Coverage

The current Fish package set contains 36 packages. The proposed schema covers
all of them with declarative fetch, download, install, bin, and action nodes.

| Pattern | Packages | Manifest support |
| --- | --- | --- |
| Fixed or redirect URL | `chatgpt-atlas`, `codex-app`, `cursor`, `discord`, `docker-desktop`, `firefox`, `github`, `google-chrome`, `iterm2`, `microsoft-auto-update`, `ollama-app`, `slack`, `steam`, `tailscale-app`, `telegram-desktop`, `visual-studio-code` | `fetch "direct"` |
| GitHub release asset | `clash-verge-rev`, `keka`, `obsidian`, `opencode-desktop`, `podman-desktop`, `rustdesk` | `fetch "github-release"` |
| JSON URL extraction | `antigravity`, `jetbrains-toolbox`, `kim`, `zed` | `request format="json"` plus `url from` |
| JSON version extraction and URL template | `gitkraken`, `parallels` | `request`, `let`, and templated `url` |
| HTML regex extraction | `beyond-compare`, `bricklink-studio`, `itermbrowserplugin`, `nomachine` | `request format="text"` plus `regex` |
| Sparkle or XML extraction | `cloudflare-warp`, `ghostty`, `wireshark-app` | `request format="sparkle"` or `format="xml"` |
| Architecture-only URL template | `unity-hub` | `let` architecture mapping plus templated `url` |

Install combinations:

| Download and install | Packages | Support |
| --- | --- | --- |
| `download "dmg"` plus `install "copy-app"` | Most GUI app DMGs | Supported |
| `download "zip"` plus `install "copy-app"` | `antigravity`, `beyond-compare`, `github`, `gitkraken`, `iterm2`, `itermbrowserplugin` | Supported |
| `download "pkg"` plus `install "run-pkg"` | `bricklink-studio`, `cloudflare-warp`, `microsoft-auto-update`, `tailscale-app` | Supported |
| `download "dmg"` plus `install "run-pkg"` | `nomachine` | Supported with `package` |

Post-install coverage:

| Current behavior | Packages | Manifest support |
| --- | --- | --- |
| CLI wrapper | `firefox`, `ghostty`, `keka`, `obsidian`, `tailscale-app`, `zed` | `bin "wrapper"` |
| CLI symlink | `antigravity`, `beyond-compare`, `cursor`, `ollama-app`, `visual-studio-code` | `bin "symlink"` |
| Unhide and remove Finder xattr | `parallels` | `action "unhide"` and `action "remove-xattr"` |

## Example Manifests

### Direct DMG App

```kdl
app "google-chrome" schema=1 {
  display-name "Google Chrome"
  bundle "Google Chrome.app"

  fetch "direct" {
    url "https://dl.google.com/chrome/mac/universal/stable/GGRO/googlechrome.dmg"
  }

  download "dmg"
  install "copy-app"
}
```

### Direct PKG Installer

```kdl
app "tailscale-app" schema=1 {
  display-name "Tailscale"
  bundle "Tailscale.app"

  fetch "direct" {
    url "https://pkgs.tailscale.com/stable/Tailscale-latest-macos.pkg"
  }

  download "pkg"
  install "run-pkg"

  bin "wrapper" name="tailscale" binary="Tailscale"
}
```

### GitHub Release Asset

```kdl
app "podman-desktop" schema=1 {
  display-name "Podman Desktop"
  bundle "Podman Desktop.app"

  fetch "github-release" repo="containers/podman-desktop" {
    asset arch="arm64" regex="podman-desktop-.*-arm64\\.dmg$"
    asset arch="x86_64" regex="podman-desktop-.*-x64\\.dmg$"
  }

  download "dmg"
  install "copy-app"
}
```

### Metadata Request with URL Extraction

```kdl
app "zed" schema=1 {
  display-name "Zed"
  bundle "Zed.app"

  fetch {
    let "arch" arm64="aarch64" x86_64="x86_64"

    request "release" format="json" {
      url "https://zed.dev/api/releases/latest?asset=Zed.dmg&stable=1&os=macos&arch={arch}"
    }

    url from="release" json=".url"
  }

  download "dmg"
  install "copy-app"

  bin "wrapper" name="zed" binary="cli"
}
```

### DMG Containing a PKG

```kdl
app "nomachine" schema=1 {
  display-name "NoMachine"
  bundle "NoMachine.app"

  fetch {
    request "page" format="text" {
      url "https://download.nomachine.com/download/?id=7&platform=mac"
    }

    url from="page" regex="id=\"link_download\" href=\"(https://[^\"]+\\.dmg)\""
  }

  download "dmg"

  install "run-pkg" {
    package "NoMachine.pkg"
  }
}
```

## Rust Architecture

The Rust rewrite should use a small workspace so parsing, resolution, and
macOS effects stay separate.

```text
orchard/
  Cargo.toml
  crates/
    orchard-cli/
    orchard-core/
    orchard-fetch/
    orchard-macos/
    orchard-migrate/
  docs/
    rust-kdl-design.md
```

### `orchard-cli`

- Owns `clap` command definitions and terminal output.
- Converts domain errors into user-facing diagnostics and exit codes.
- Avoids business logic except command orchestration.

### `orchard-core`

- Defines manifest structs and enums.
- Parses KDL into typed manifests.
- Applies defaults and validates cross-field rules.
- Builds install plans from resolved package metadata.
- Contains no direct process execution.

### `orchard-fetch`

- Resolves final URLs from `fetch` definitions.
- Implements direct URLs, GitHub release asset selection, metadata requests,
  selector extraction, and template interpolation.
- Uses typed errors for HTTP, selector, template, and ambiguity failures.

### `orchard-macos`

- Wraps macOS operations behind traits.
- Handles DMG mount and unmount, ZIP extraction, `ditto`, `installer`,
  `osascript`, app version reads, and post-install side effects.
- Exposes mockable interfaces for tests.

### `orchard-migrate`

- Provides migration helpers from existing Fish package definitions.
- Converts simple static packages automatically.
- Emits reviewable KDL drafts for dynamic packages.
- Never preserves Fish callbacks as runtime behavior.

## Validation

`orchard validate` should support two levels.

- **Static validation**: parse KDL, check schema, ID, required nodes, supported
  enum values, template variables, architecture coverage, install/download
  compatibility, and post-install references.
- **Resolution validation**: optionally execute fetch requests to confirm
  selectors resolve to a valid URL for the current host architecture.

Static validation must not require network access. Resolution validation may be
enabled with a flag such as `--resolve`.

Important cross-field checks:

- `app` ID matches the file name.
- `download` is one of `dmg`, `zip`, or `pkg`.
- `install "copy-app"` is only valid for `dmg` and `zip`.
- `install "run-pkg"` is valid for `pkg` or `dmg`.
- `install "run-pkg"` with `download "dmg"` requires `package`.
- `bin` nodes require a `bundle` path.
- Architecture mappings cover `arm64` and `x86_64` when architecture-specific
  selection is used.

## Install Flow

- Load and validate the manifest.
- Resolve the final URL through `fetch`.
- Derive the cache path from app ID, URL hash, and download format.
- Validate an existing cached file if present.
- Download or resume the file.
- Quit the app when a bundle exists and the manifest allows quit behavior.
- Perform the install operation.
- Run declared `bin` and `action` side effects.
- Re-read installed state and print the result.

## Error Handling

The Rust implementation should use typed domain errors inside libraries and
convert them into readable CLI diagnostics at the boundary.

- Use `thiserror` for core, fetch, and macOS error enums.
- Use contextual CLI reporting in `orchard-cli`.
- Avoid panics and `unwrap` outside tests.
- Include app ID and manifest path in user-facing errors when possible.
- Include the failing node or field path for manifest validation errors.

## Testing Strategy

- Unit test KDL parsing and defaulting.
- Unit test validation rules with fixture manifests.
- Unit test fetch selectors against saved JSON, HTML, XML, and Sparkle
  fixtures.
- Snapshot test install plans for representative packages.
- Mock macOS command execution for install operations.
- Keep a small number of host integration tests behind an explicit opt-in.

The current Fish validation tests should be replaced by Rust fixture tests that
exercise the same behaviors: valid packages pass, ID mismatches fail, missing
URLs fail, and package-local state cannot leak between manifests.

## Migration Strategy

- Add Rust Orchard alongside the current Fish implementation during
  development.
- Create KDL manifests under `home/dot_config/orchard/apps`.
- Convert static direct packages first.
- Convert GitHub release packages next.
- Convert general fetch pipeline packages with fixtures for each upstream
  metadata response.
- Remove runtime Fish package loading after all current packages have KDL
  equivalents.
- Keep old Fish package files only as source-control history, not as runtime
  compatibility.

## Open Design Decisions

- Choose the KDL parser crate and whether it should map directly into typed
  structs or through an intermediate AST.
- Decide whether `xml` selectors are needed in schema v1 or whether
  `sparkle` plus `regex` over text covers the current package set.
- Decide the exact package receipt fields for package-only installed-state
  checks.
- Decide whether `validate --resolve` should be opt-in globally or per app.
