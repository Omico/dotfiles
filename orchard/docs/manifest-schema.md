# Orchard KDL Manifest Schema

## Purpose

Orchard packages are declarative KDL files. They replace executable Fish package
definitions while keeping package authoring small, readable, and strongly
validated.

Each app is described by one file:

```text
home/dot_config/orchard/apps/<app_id>.kdl
```

## Model

The top-level `app` node describes cross-platform product identity. Each
`platform` block describes how that product is fetched, downloaded, installed,
and wired into one host platform.

```kdl
app "firefox" schema=1 {
  display-name "Firefox"

  platform "macos" {
    bundle "Firefox.app"

    fetch "direct" {
      url "https://download.mozilla.org/?product=firefox-latest-ssl&os=osx"
    }

    download "dmg"
    install "copy-app"

    bin "wrapper" name="firefox"
  }
}
```

## Top-Level App Nodes

- `app` argument: package ID. It must match the file name.
- `schema`: manifest schema version.
- `display-name`: human-facing product name used in output.

Top-level nodes must stay portable. Platform-specific nodes such as `bundle`,
`fetch`, `download`, `install`, `bin`, and `action` must live inside a
`platform` block.

## Platform Blocks

```kdl
platform "macos" {
  bundle "Visual Studio Code.app"

  fetch "direct" {
    url "https://code.visualstudio.com/sha/download?build=stable&os=darwin-universal-dmg"
  }

  download "dmg"
  install "copy-app"
}
```

- `platform` argument: platform ID, such as `macos`, `windows`, or `linux`.
- Schema v1 only executes `platform "macos"`.
- Non-macOS platform blocks may be parsed and ignored by default.
- Non-macOS platform blocks should be validated only when an explicit
  all-platform validation mode is requested.

## macOS Identity

Inside `platform "macos"`, `bundle` describes the installed `.app` bundle. The
default path is `/Applications/<bundle>`.

```kdl
bundle "Firefox.app" quit=true
```

`bundle` may override the installed path:

```kdl
bundle "Microsoft AutoUpdate.app" path="/Library/Application Support/Microsoft/MAU2.0/Microsoft AutoUpdate.app"
```

When `quit` is omitted and a bundle exists, Orchard should preserve the current
behavior: ask the running app to quit before replacing it.

For packages that do not install a durable app bundle, use an explicit
installed-state node:

```kdl
installed "pkg-receipt" id="com.example.pkg"
```

## Fetch

`fetch` resolves the final download URL for a platform. It may also expose
variables such as a release version.

Direct or redirecting URL:

```kdl
fetch "direct" {
  url "https://slack.com/api/desktop.latestRelease?arch=universal&variant=dmg&redirect=true"
}
```

GitHub latest release asset:

```kdl
fetch "github-release" repo="containers/podman-desktop" {
  asset arch="arm64" regex="podman-desktop-.*-arm64\\.dmg$"
  asset arch="x86_64" regex="podman-desktop-.*-x64\\.dmg$"
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

The general form exists for packages that need to request metadata, extract a
value, and use it either as the final URL or inside a URL template.

## Fetch Statements

- **`let` with architecture mapping**: maps the host architecture to a manifest
  variable.
- **`request`**: downloads metadata as `json`, `text`, `xml`, or `sparkle`.
- **`let` from request**: extracts a variable from a named request.
- **`url` literal**: sets the final URL from a template.
- **`url from`**: extracts the final URL from a named request.
- **`version`**: optionally extracts a version string for list output and cache
  metadata.

JSON version extraction and URL template:

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

HTML regex extraction:

```kdl
fetch {
  request "page" format="text" {
    url "https://www.bricklink.com/v3/studio/download.page"
  }

  let "version" from="page" regex="\"strVersion\"\\s*:\\s*\"([^\"]+)\""

  url "https://studio.download.bricklink.info/Studio2.0/Archive/{version}/Studio+2.0.pkg"
}
```

JSON object key helper:

```kdl
fetch {
  request "index" format="json" {
    url "https://download.parallels.com/website_links/desktop/index.json"
  }

  let "major_version" from="index" json-key="max-numeric"

  url "https://link.parallels.com/pdfm/v{major_version}/dmg-download"
}
```

XML text extraction:

```kdl
fetch {
  request "appcast" format="xml" {
    url "https://www.wireshark.org/update/0/Wireshark/0.0.0/macOS/arm64/en-US/stable.xml"
  }

  let "version" from="appcast" xml-text="//*[local-name()='shortVersionString']"

  url "https://www.wireshark.org/download/osx/all-versions/Wireshark%20{version}.dmg"
}
```

Sparkle enclosure extraction:

```kdl
fetch {
  request "appcast" format="sparkle" {
    url "https://release.files.ghostty.org/appcast.xml"
  }

  url from="appcast" sparkle-enclosure-contains="Ghostty.dmg"
}
```

## Selector Semantics

Selectors are schema features, not an embedded programming language.

- `json`: a jq-lite path expression over objects and arrays.
- `json-key`: object-key selection helpers, starting with `max-numeric`.
- `regex`: a regular expression over text; the first capture group is used.
- `sparkle-enclosure-contains`: selects the last Sparkle enclosure URL whose
  URL contains the given substring.
- `xml-text`: a narrow XPath-like selector that returns normalized text.

If extraction yields no value, more than one ambiguous value, or an invalid
URL, validation should fail with an error pointing to the manifest field.

## Template Variables

Templates may reference:

- Host variables exposed by Orchard, such as `{host.arch}`.
- Variables created by `let`, such as `{arch}` or `{version}`.
- Package identity variables, such as `{app.id}` and `{app.display_name}`.

Templates must not execute code. Missing variables are validation errors.

## Download

`download` describes the cached file format.

```kdl
download "dmg"
```

Supported macOS formats:

- `dmg`: validate with DMG image checks and mount tests.
- `zip`: validate with ZIP archive checks.
- `pkg`: validate with macOS package signature or package metadata checks.

The cache key should default to a stable hash of the resolved final URL and the
download format.

## Install

`install` describes what Orchard does with the downloaded file.

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

Supported macOS install operations:

- `copy-app`: find the configured app bundle inside a mounted DMG or extracted
  ZIP, then copy it to the configured bundle path.
- `run-pkg`: run the macOS installer for a downloaded PKG, or for a named PKG
  found inside a mounted DMG.

The names are intentionally action-oriented. `download "pkg"` describes the
file format, while `install "run-pkg"` describes the operation.

## Post-Install Side Effects

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

Other allowed macOS actions:

```kdl
action "unhide"
action "remove-xattr" name="com.apple.FinderInfo"
action "open"
```

## Complete Examples

Direct DMG app:

```kdl
app "google-chrome" schema=1 {
  display-name "Google Chrome"

  platform "macos" {
    bundle "Google Chrome.app"

    fetch "direct" {
      url "https://dl.google.com/chrome/mac/universal/stable/GGRO/googlechrome.dmg"
    }

    download "dmg"
    install "copy-app"
  }
}
```

Direct PKG installer:

```kdl
app "tailscale-app" schema=1 {
  display-name "Tailscale"

  platform "macos" {
    bundle "Tailscale.app"

    fetch "direct" {
      url "https://pkgs.tailscale.com/stable/Tailscale-latest-macos.pkg"
    }

    download "pkg"
    install "run-pkg"

    bin "wrapper" name="tailscale" binary="Tailscale"
  }
}
```

DMG containing a PKG:

```kdl
app "nomachine" schema=1 {
  display-name "NoMachine"

  platform "macos" {
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
}
```

Future platform block shape:

```kdl
app "example" schema=1 {
  display-name "Example"

  platform "windows" {
    fetch "direct" {
      url "https://example.com/ExampleSetup.exe"
    }

    download "exe"
    install "run-installer" {
      arg "/S"
    }
  }
}
```

The Windows block illustrates the intended shape only. Schema v1 does not
execute or fully validate Windows install semantics.
