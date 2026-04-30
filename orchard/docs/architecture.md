# Orchard Runtime Design

## Purpose

The Rust implementation keeps manifest logic, fetch resolution, and macOS side
effects in separate crates so each part is testable without relying on host
state.

## Workspace

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
    README.md
    manifest-schema.md
    architecture.md
    fish-to-kdl-migration.md
    implementation-plan.md
```

## Crates

### `orchard-cli`

- Owns `clap` command definitions and terminal output.
- Converts domain errors into user-facing diagnostics and exit codes.
- Avoids business logic except command orchestration.

### `orchard-core`

- Defines manifest structs and enums.
- Parses KDL into typed manifests.
- Applies defaults and validates cross-field rules.
- Selects the active platform implementation for the host.
- Builds install plans from resolved package metadata.
- Contains no direct process execution.

### `orchard-fetch`

- Resolves final URLs from platform `fetch` definitions.
- Implements direct URLs, GitHub release asset selection, metadata requests,
  selector extraction, and template interpolation.
- Uses typed errors for HTTP, selector, template, and ambiguity failures.

### `orchard-macos`

- Wraps macOS operations behind traits.
- Handles DMG mount and unmount, ZIP extraction, `ditto`, `installer`,
  `osascript`, app version reads, locking, and post-install side effects.
- Exposes mockable interfaces for tests.

### `orchard-migrate`

- Provides migration helpers from existing Fish package definitions.
- Converts simple static packages automatically.
- Emits reviewable KDL drafts for dynamic packages.
- Never preserves Fish callbacks as runtime behavior.

## Platform Policy

Schema v1 supports multiple `platform` blocks in a manifest, but only
`platform "macos"` is executable. The Rust architecture should keep the
backend boundary clear so future `orchard-linux` or `orchard-windows` crates
can be added without rewriting manifest parsing.

Validation defaults to the host platform. A future `--all-platforms` mode may
parse and validate non-host blocks, but non-macOS install semantics are not
part of v1.

## Validation

`orchard validate` should support two levels.

- **Static validation**: parse KDL, check schema, ID, required nodes, supported
  platform nodes, enum values, template variables, architecture coverage,
  install/download compatibility, and post-install references.
- **Resolution validation**: optionally execute fetch requests to confirm
  selectors resolve to a valid URL for the selected platform and host
  architecture.

Static validation must not require network access. Resolution validation may be
enabled with a flag such as `--resolve`.

Important cross-field checks:

- `app` ID matches the file name.
- A v1 package has a `platform "macos"` block before it is executable.
- `download` is one of `dmg`, `zip`, or `pkg` inside `platform "macos"`.
- `install "copy-app"` is only valid for `dmg` and `zip`.
- `install "run-pkg"` is valid for `pkg` or `dmg`.
- `install "run-pkg"` with `download "dmg"` requires `package`.
- `bin` nodes require a `bundle` path.
- Architecture mappings cover `arm64` and `x86_64` when architecture-specific
  selection is used.

## Install Flow

- Load and statically validate the manifest.
- Select the host platform block.
- Resolve the final URL through the selected platform `fetch`.
- Derive the cache path from app ID, platform ID, URL hash, and download
  format.
- Validate an existing cached file if present.
- Download or resume the file.
- Quit the app when a bundle exists and the manifest allows quit behavior.
- Perform the install operation.
- Run declared `bin` and `action` side effects.
- Re-read installed state and print the result.

## Concurrency Model

Orchard should treat installation as a staged pipeline. The safe concurrency
boundary is between preparation work and system mutation work.

- **Fetch resolution**: may run concurrently because it only performs network
  metadata requests and template resolution.
- **Download**: may run concurrently when cache writes are protected by a cache
  lock for the target archive path.
- **Install**: must run serially by default because it mutates global macOS
  state: `/Applications`, `/usr/local/bin`, mounted DMG volumes, installer
  receipts, and privilege prompts.
- **Post-install side effects**: run serially with the matching app install.

The first Rust implementation should include lock and scheduling concepts even
if the CLI initially installs one app at a time:

- **Per-app lock**: prevents two Orchard processes from installing the same app
  concurrently.
- **Per-cache-entry lock**: prevents duplicate downloads from writing the same
  archive.
- **Global install lock**: prevents overlapping system mutation phases.

A future multi-app command can then use the same model:

```text
orchard install app-a app-b app-c --jobs 4
```

In that mode, `--jobs` would limit concurrent fetch and download work while the
global install lock keeps the actual install phase serialized.

## Error Handling

The Rust implementation should use typed domain errors inside libraries and
convert them into readable CLI diagnostics at the boundary.

- Use `thiserror` for core, fetch, and macOS error enums.
- Use contextual CLI reporting in `orchard-cli`.
- Avoid panics and `unwrap` outside tests.
- Include app ID, platform ID, and manifest path in user-facing errors when
  possible.
- Include the failing node or field path for manifest validation errors.

## Testing Strategy

- Unit test KDL parsing and defaulting.
- Unit test platform selection and validation rules with fixture manifests.
- Unit test fetch selectors against saved JSON, HTML, XML, and Sparkle
  fixtures.
- Snapshot test install plans for representative packages.
- Mock macOS command execution for install operations.
- Keep a small number of host integration tests behind an explicit opt-in.

The current Fish validation tests should be replaced by Rust fixture tests that
exercise the same behaviors: valid packages pass, ID mismatches fail, missing
URLs fail, and package-local state cannot leak between manifests.
