# Orchard Rust and KDL Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Rust version of Orchard that uses declarative KDL manifests
instead of executable Fish app packages.

**Architecture:** The implementation is split into small Rust crates:
`orchard-cli` owns command-line behavior, `orchard-core` owns typed manifests
and validation, `orchard-fetch` resolves final download URLs, `orchard-macos`
wraps macOS effects behind testable interfaces, and `orchard-migrate` helps
convert existing Fish packages to KDL. KDL manifests follow the
`app -> platform -> fetch -> download -> install` model described in
`orchard/docs/manifest-schema.md`. The execution model in
`orchard/docs/architecture.md` separates concurrent fetch and download
preparation from the serialized macOS install phase.

**Tech Stack:** Rust, Cargo workspace, `clap`, official `kdl` crate,
`thiserror`, `miette`, `reqwest`, `serde_json`, `regex`, `tempfile`, and
mockable process execution wrappers.

---

## Scope

The plan implements the first usable Rust Orchard with:

- KDL package parsing and static validation.
- Top-level app identity with one or more platform blocks.
- Executable support for `platform "macos"`.
- Direct URL, GitHub release, JSON, text regex, XML, and Sparkle fetch support.
- DMG, ZIP, and PKG download cache handling.
- `copy-app` and `run-pkg` install operations.
- Declared `bin` and `action` post-install side effects.
- A staged install coordinator with per-app, per-cache-entry, and global
  install locks.
- CLI commands matching the existing Fish surface.
- KDL manifests for all current Orchard packages.

The plan does not include a GUI, background updates, arbitrary package scripts,
fully parallel system install phases, Linux or Windows install backends, or a
general plugin system.

## File Structure

- Create: `orchard/Cargo.toml`
- Create: `orchard/crates/orchard-cli/Cargo.toml`
- Create: `orchard/crates/orchard-cli/src/main.rs`
- Create: `orchard/crates/orchard-cli/src/commands.rs`
- Create: `orchard/crates/orchard-core/Cargo.toml`
- Create: `orchard/crates/orchard-core/src/lib.rs`
- Create: `orchard/crates/orchard-core/src/manifest.rs`
- Create: `orchard/crates/orchard-core/src/parse.rs`
- Create: `orchard/crates/orchard-core/src/platform.rs`
- Create: `orchard/crates/orchard-core/src/validate.rs`
- Create: `orchard/crates/orchard-core/src/plan.rs`
- Create: `orchard/crates/orchard-core/src/scheduler.rs`
- Create: `orchard/crates/orchard-fetch/Cargo.toml`
- Create: `orchard/crates/orchard-fetch/src/lib.rs`
- Create: `orchard/crates/orchard-fetch/src/github.rs`
- Create: `orchard/crates/orchard-fetch/src/pipeline.rs`
- Create: `orchard/crates/orchard-fetch/src/selectors.rs`
- Create: `orchard/crates/orchard-fetch/src/template.rs`
- Create: `orchard/crates/orchard-macos/Cargo.toml`
- Create: `orchard/crates/orchard-macos/src/lib.rs`
- Create: `orchard/crates/orchard-macos/src/command.rs`
- Create: `orchard/crates/orchard-macos/src/download.rs`
- Create: `orchard/crates/orchard-macos/src/install.rs`
- Create: `orchard/crates/orchard-macos/src/locks.rs`
- Create: `orchard/crates/orchard-macos/src/side_effects.rs`
- Create: `orchard/crates/orchard-migrate/Cargo.toml`
- Create: `orchard/crates/orchard-migrate/src/lib.rs`
- Create: `orchard/tests/fixtures/apps/*.kdl`
- Create: `orchard/tests/fixtures/fetch/*`
- Modify: `home/dot_config/fish/completions/orchard.fish`
- Modify: `orchard/docs/manifest-schema.md`
- Modify: `orchard/docs/architecture.md`
- Modify: `orchard/docs/fish-to-kdl-migration.md`

## Task: Workspace Scaffold

**Files:**

- Create: `orchard/Cargo.toml`
- Create: `orchard/crates/orchard-cli/Cargo.toml`
- Create: `orchard/crates/orchard-core/Cargo.toml`
- Create: `orchard/crates/orchard-fetch/Cargo.toml`
- Create: `orchard/crates/orchard-macos/Cargo.toml`
- Create: `orchard/crates/orchard-migrate/Cargo.toml`
- Create: minimal `src/lib.rs` or `src/main.rs` for each crate

- [ ] **Step: Create workspace manifest**

Use this workspace shape:

```toml
[workspace]
members = [
  "crates/orchard-cli",
  "crates/orchard-core",
  "crates/orchard-fetch",
  "crates/orchard-macos",
  "crates/orchard-migrate",
]
resolver = "2"

[workspace.package]
edition = "2024"
license = "MIT"

[workspace.dependencies]
clap = { version = "4", features = ["derive"] }
kdl = "6"
miette = { version = "7", features = ["fancy"] }
regex = "1"
reqwest = { version = "0.12", features = ["blocking", "json"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
tempfile = "3"
thiserror = "2"
```

- [ ] **Step: Add crate dependency wiring**

`orchard-cli` depends on `orchard-core`, `orchard-fetch`, and
`orchard-macos`. `orchard-fetch` depends on `orchard-core`.
`orchard-migrate` depends on `orchard-core`.

- [ ] **Step: Verify workspace compiles**

Run:

```bash
cargo check --manifest-path orchard/Cargo.toml
```

Expected: Cargo builds all empty crates successfully.

- [ ] **Step: Commit scaffold**

```bash
git add orchard/Cargo.toml orchard/crates
git commit -m "feat: Scaffold Orchard Rust workspace"
```

## Task: Manifest Model and Parser

**Files:**

- Create: `orchard/crates/orchard-core/src/manifest.rs`
- Create: `orchard/crates/orchard-core/src/parse.rs`
- Create: `orchard/crates/orchard-core/src/platform.rs`
- Modify: `orchard/crates/orchard-core/src/lib.rs`
- Test: `orchard/crates/orchard-core/src/parse.rs`

- [ ] **Step: Define typed manifest structs**

Create enums and structs for `PlatformId`, `PlatformManifest`,
`DownloadFormat`, `InstallOperation`, `Fetch`, `FetchStep`, `Bin`, `Action`,
`Bundle`, and `InstalledState`.

The public root type should be:

```rust
pub struct AppManifest {
    pub id: String,
    pub schema: u32,
    pub display_name: String,
    pub platforms: Vec<PlatformManifest>,
}

pub struct PlatformManifest {
    pub id: PlatformId,
    pub bundle: Option<Bundle>,
    pub installed: Option<InstalledState>,
    pub fetch: Fetch,
    pub download: DownloadFormat,
    pub install: InstallOperation,
    pub bins: Vec<Bin>,
    pub actions: Vec<Action>,
}
```

- [ ] **Step: Implement KDL parsing into typed structs**

Parse `app "<id>" schema=1 { ... }` using `kdl::KdlDocument`, parse nested
`platform "<id>" { ... }` blocks, then convert nodes into the typed model.
Return a typed parse error that includes the manifest path and field name.

- [ ] **Step: Add parser tests**

Cover these fixtures in unit tests:

```rust
#[test]
fn parse_accepts_direct_dmg_copy_app_manifest() { /* firefox fixture */ }

#[test]
fn parse_keeps_macos_fields_inside_platform_block() { /* chrome fixture */ }

#[test]
fn parse_accepts_github_release_arch_assets() { /* podman fixture */ }

#[test]
fn parse_accepts_general_fetch_pipeline() { /* zed fixture */ }

#[test]
fn parse_accepts_wrapper_with_fixed_args() { /* keka fixture */ }
```

- [ ] **Step: Verify parser tests pass**

Run:

```bash
cargo test --manifest-path orchard/Cargo.toml -p orchard-core parse
```

Expected: parser unit tests pass.

- [ ] **Step: Commit parser**

```bash
git add orchard/crates/orchard-core
git commit -m "feat: Parse Orchard KDL manifests"
```

## Task: Static Validation

**Files:**

- Create: `orchard/crates/orchard-core/src/validate.rs`
- Modify: `orchard/crates/orchard-core/src/lib.rs`
- Test: `orchard/crates/orchard-core/src/validate.rs`

- [ ] **Step: Implement validation rules**

Validation must check:

- File stem matches `app` ID.
- `schema` is supported.
- `display-name` is non-empty.
- Top-level app nodes do not contain platform-only nodes such as `bundle`,
  `fetch`, `download`, `install`, `bin`, or `action`.
- A v1 executable package has a `platform "macos"` block.
- `download` inside `platform "macos"` is `dmg`, `zip`, or `pkg`.
- `install "copy-app"` only pairs with `download "dmg"` or `download "zip"`.
- `install "run-pkg"` only pairs with `download "pkg"` or `download "dmg"`.
- `install "run-pkg"` with `download "dmg"` includes `package`.
- `bin` nodes require a `bundle`.
- Architecture mappings cover `arm64` and `x86_64` when used.
- Template variables are declared before use.

- [ ] **Step: Add validation tests**

Use tests with one behavior each:

```rust
#[test]
fn validate_rejects_id_that_does_not_match_file_stem() { /* assert error */ }

#[test]
fn validate_rejects_top_level_bundle_node() { /* assert error */ }

#[test]
fn validate_rejects_missing_macos_platform_for_executable_package() { /* assert error */ }

#[test]
fn validate_rejects_copy_app_from_pkg_download() { /* assert error */ }

#[test]
fn validate_rejects_run_pkg_from_dmg_without_package_name() { /* assert error */ }

#[test]
fn validate_rejects_bin_without_bundle() { /* assert error */ }

#[test]
fn validate_rejects_missing_template_variable() { /* assert error */ }
```

- [ ] **Step: Verify validation tests pass**

Run:

```bash
cargo test --manifest-path orchard/Cargo.toml -p orchard-core validate
```

Expected: validation unit tests pass.

- [ ] **Step: Commit validation**

```bash
git add orchard/crates/orchard-core
git commit -m "feat: Validate Orchard KDL manifests"
```

## Task: Fetch Engine

**Files:**

- Create: `orchard/crates/orchard-fetch/src/lib.rs`
- Create: `orchard/crates/orchard-fetch/src/github.rs`
- Create: `orchard/crates/orchard-fetch/src/pipeline.rs`
- Create: `orchard/crates/orchard-fetch/src/selectors.rs`
- Create: `orchard/crates/orchard-fetch/src/template.rs`
- Create: `orchard/tests/fixtures/fetch/`

- [ ] **Step: Define fetch output**

The fetch crate resolves a selected `PlatformManifest` and should return:

```rust
pub struct ResolvedFetch {
    pub url: String,
    pub version: Option<String>,
    pub variables: std::collections::BTreeMap<String, String>,
}
```

- [ ] **Step: Implement direct fetch**

`fetch "direct"` returns the configured URL without network access.

- [ ] **Step: Implement GitHub release asset selection**

Fetch latest release JSON, choose the first matching asset regex for the host
architecture, and return `browser_download_url`.

- [ ] **Step: Implement pipeline requests and selectors**

Support:

- `format="json"` with `json` and `json-key="max-numeric"`.
- `format="text"` with `regex`.
- `format="xml"` with `xml-text`.
- `format="sparkle"` with `sparkle-enclosure-contains`.

- [ ] **Step: Implement template interpolation**

Templates may use `{host.arch}`, `let` variables, and extracted variables.
Missing variables produce typed errors.

- [ ] **Step: Add fixture-based tests**

Add saved upstream responses for representative current packages:

- `zed-release.json`
- `gitkraken-releases-arm64.json`
- `parallels-index.json`
- `bricklink-download.html`
- `ghostty-appcast.xml`
- `wireshark-stable.xml`

Test final URLs for each fixture.

- [ ] **Step: Verify fetch tests pass**

Run:

```bash
cargo test --manifest-path orchard/Cargo.toml -p orchard-fetch
```

Expected: fetch unit tests pass without live network access.

- [ ] **Step: Commit fetch engine**

```bash
git add orchard/crates/orchard-fetch orchard/tests/fixtures/fetch
git commit -m "feat: Resolve Orchard fetch pipelines"
```

## Task: Download Cache and macOS Operations

**Files:**

- Create: `orchard/crates/orchard-macos/src/command.rs`
- Create: `orchard/crates/orchard-macos/src/download.rs`
- Create: `orchard/crates/orchard-macos/src/install.rs`
- Create: `orchard/crates/orchard-macos/src/locks.rs`
- Create: `orchard/crates/orchard-macos/src/side_effects.rs`
- Modify: `orchard/crates/orchard-macos/src/lib.rs`

- [ ] **Step: Define process runner trait**

Create a trait that can be mocked:

```rust
pub trait CommandRunner {
    fn run(&self, program: &str, args: &[&str]) -> Result<CommandOutput, MacosError>;
}
```

- [ ] **Step: Implement cache path derivation**

Use app ID, resolved URL hash, and download format to produce paths compatible
with the current cache behavior.

- [ ] **Step: Implement filesystem lock helpers**

Create lock helpers for:

- Per-app lock paths under the Orchard cache directory.
- Per-cache-entry lock paths next to the target archive.
- A global install lock path under the Orchard cache directory.

The lock API should be explicit:

```rust
pub enum OrchardLockKind {
    App { app_id: String },
    CacheEntry { cache_path: std::path::PathBuf },
    GlobalInstall,
}

pub trait LockManager {
    fn acquire(&self, kind: OrchardLockKind) -> Result<LockGuard, MacosError>;
}
```

- [ ] **Step: Implement cache validation wrappers**

Use macOS tools through `CommandRunner`:

- DMG: `hdiutil imageinfo` plus trial attach.
- ZIP: `unzip -t`.
- PKG: `pkgutil --check-signature`.

- [ ] **Step: Implement install operations**

Support:

- `copy-app` from mounted DMG.
- `copy-app` from extracted ZIP.
- `run-pkg` from downloaded PKG.
- `run-pkg` from mounted DMG with a package name.

- [ ] **Step: Implement declared side effects**

Support:

- `bin "wrapper"` with optional `binary` and fixed `arg` entries.
- `bin "symlink"`.
- `action "unhide"`.
- `action "remove-xattr"`.
- `action "open"`.

- [ ] **Step: Add mock-runner tests**

Test that each operation emits the expected command sequence without touching
the host filesystem.

- [ ] **Step: Verify macOS crate tests pass**

Run:

```bash
cargo test --manifest-path orchard/Cargo.toml -p orchard-macos
```

Expected: macOS wrapper tests pass with the mock runner.

- [ ] **Step: Commit macOS operations**

```bash
git add orchard/crates/orchard-macos
git commit -m "feat: Add macOS install operations"
```

## Task: Install Scheduling

**Files:**

- Create: `orchard/crates/orchard-core/src/scheduler.rs`
- Modify: `orchard/crates/orchard-core/src/lib.rs`
- Modify: `orchard/crates/orchard-cli/src/commands.rs`

- [ ] **Step: Define staged install plan**

Represent the install pipeline as explicit stages:

```rust
pub enum InstallStage {
    Fetch,
    Download,
    Install,
    SideEffects,
}

pub struct InstallJob {
    pub app_id: String,
    pub stages: Vec<InstallStage>,
}
```

- [ ] **Step: Define concurrency policy**

The default policy allows concurrent preparation work in the model, but keeps
the system mutation phase serialized:

```rust
pub struct ConcurrencyPolicy {
    pub fetch_jobs: usize,
    pub download_jobs: usize,
    pub serialize_installs: bool,
}

impl Default for ConcurrencyPolicy {
    fn default() -> Self {
        Self {
            fetch_jobs: 4,
            download_jobs: 2,
            serialize_installs: true,
        }
    }
}
```

- [ ] **Step: Implement scheduler tests**

Add unit tests that prove:

- Fetch stages can be grouped before install stages.
- Download stages require cache-entry locks.
- Install and side-effect stages require the global install lock.
- The default policy serializes install stages even when preparation jobs are
  greater than one.

- [ ] **Step: Wire single-app install through the scheduler**

The first CLI may still accept one app ID, but it should use the staged
scheduler path. This avoids a second control flow when multi-app install is
added later.

- [ ] **Step: Verify scheduler tests pass**

Run:

```bash
cargo test --manifest-path orchard/Cargo.toml -p orchard-core scheduler
```

Expected: scheduler unit tests pass.

- [ ] **Step: Commit install scheduling**

```bash
git add orchard/crates/orchard-core orchard/crates/orchard-cli
git commit -m "feat: Add Orchard install scheduling model"
```

## Task: CLI Commands

**Files:**

- Create: `orchard/crates/orchard-cli/src/main.rs`
- Create: `orchard/crates/orchard-cli/src/commands.rs`
- Modify: `orchard/crates/orchard-cli/Cargo.toml`

- [ ] **Step: Define command surface**

Use `clap` for:

```text
orchard list
orchard validate [--resolve] [app_id ...]
orchard validate --all-platforms [app_id ...]
orchard install <app_id> [--force]
orchard migrate brew [--plan]
orchard cleanup
```

- [ ] **Step: Implement config and cache path discovery**

Respect `XDG_CONFIG_HOME` and `XDG_CACHE_HOME`, defaulting to
`~/.config/orchard` and `~/.cache/orchard`.

- [ ] **Step: Implement `list`**

Load KDL manifests, compute installed state through `orchard-macos`, and print
the app ID with installed status and version when available.

- [ ] **Step: Implement `validate`**

Run static validation by default. With `--resolve`, run fetch resolution for
the current host platform and architecture. With `--all-platforms`, parse and
validate all platform blocks that have implemented schema rules.

- [ ] **Step: Implement `install`**

Load, validate, select `platform "macos"`, resolve, download, install, and run
declared side effects through the staged scheduler. Honor `--force` when the
app is already installed.

- [ ] **Step: Implement `cleanup`**

Remove the Orchard cache directory and report the cleared path.

- [ ] **Step: Add CLI integration tests**

Use temporary XDG directories and fixture manifests to test `validate` and
`list` without network or privileged commands.

- [ ] **Step: Verify CLI tests pass**

Run:

```bash
cargo test --manifest-path orchard/Cargo.toml -p orchard-cli
```

Expected: CLI tests pass.

- [ ] **Step: Commit CLI**

```bash
git add orchard/crates/orchard-cli
git commit -m "feat: Add Orchard Rust CLI"
```

## Task: KDL Package Migration

**Files:**

- Create: `home/dot_config/orchard/apps/*.kdl`
- Create: `orchard/tests/fixtures/apps/*.kdl`
- Create: `orchard/crates/orchard-migrate/src/lib.rs`

- [ ] **Step: Convert direct URL packages**

Convert packages covered by `fetch "direct"`:

- `chatgpt-atlas`
- `codex-app`
- `cursor`
- `discord`
- `docker-desktop`
- `firefox`
- `github`
- `google-chrome`
- `iterm2`
- `microsoft-auto-update`
- `ollama-app`
- `slack`
- `steam`
- `tailscale-app`
- `telegram-desktop`
- `visual-studio-code`

- [ ] **Step: Convert GitHub release packages**

Convert:

- `clash-verge-rev`
- `keka`
- `obsidian`
- `opencode-desktop`
- `podman-desktop`
- `rustdesk`

- [ ] **Step: Convert general fetch pipeline packages**

Convert:

- `antigravity`
- `beyond-compare`
- `bricklink-studio`
- `cloudflare-warp`
- `ghostty`
- `gitkraken`
- `itermbrowserplugin`
- `jetbrains-toolbox`
- `kim`
- `nomachine`
- `parallels`
- `unity-hub`
- `wireshark-app`
- `zed`

- [ ] **Step: Add migration helper diagnostics**

`orchard-migrate` should parse common Fish variable assignments and emit KDL
drafts for direct packages. Dynamic packages should be matched by known package
ID and converted through explicit Rust mapping code. All generated behavior
must be nested under `platform "macos"`.

- [ ] **Step: Validate every converted package**

Run:

```bash
cargo run --manifest-path orchard/Cargo.toml -p orchard-cli -- validate
```

Expected: every KDL package passes static validation.

- [ ] **Step: Commit converted packages**

```bash
git add home/dot_config/orchard/apps orchard/tests/fixtures/apps orchard/crates/orchard-migrate
git commit -m "feat: Convert Orchard packages to KDL"
```

## Task: Shell Integration and Documentation

**Files:**

- Modify: `home/dot_config/fish/completions/orchard.fish`
- Modify: `orchard/docs/README.md`
- Modify: `orchard/docs/manifest-schema.md`
- Modify: `orchard/docs/architecture.md`
- Modify: `orchard/docs/fish-to-kdl-migration.md`
- Modify: `orchard/docs/implementation-plan.md`
- Create: `orchard/README.md`

- [ ] **Step: Update Fish completions**

Completions should read `*.kdl` app IDs and include `--resolve` and
`--all-platforms` for `validate`.

- [ ] **Step: Add README**

`orchard/README.md` should explain how to build, validate, and install with the
Rust CLI.

- [ ] **Step: Update design doc with final parser choice**

Record the official `kdl` crate as the schema parser and confirm that schema
v1 uses top-level app identity plus nested platform blocks.

- [ ] **Step: Run Markdown lint**

Run:

```bash
npx --yes markdownlint-cli2 orchard/**/*.md --config .markdownlint-cli2.yaml
```

Expected: Markdown lint reports `0 error(s)`.

- [ ] **Step: Commit docs and completions**

```bash
git add home/dot_config/fish/completions/orchard.fish orchard/docs orchard/README.md
git commit -m "docs: Document Orchard Rust workflow"
```

## Task: Final Verification

**Files:**

- No new files expected.

- [ ] **Step: Run Rust checks**

Run:

```bash
cargo fmt --manifest-path orchard/Cargo.toml --check
cargo clippy --manifest-path orchard/Cargo.toml --all-targets --all-features -- -D warnings
cargo test --manifest-path orchard/Cargo.toml
```

Expected: all checks pass.

- [ ] **Step: Run package validation**

Run:

```bash
cargo run --manifest-path orchard/Cargo.toml -p orchard-cli -- validate
```

Expected: all KDL packages pass static validation.

- [ ] **Step: Run resolved validation for representative packages**

Run:

```bash
cargo run --manifest-path orchard/Cargo.toml -p orchard-cli -- validate --resolve zed
cargo run --manifest-path orchard/Cargo.toml -p orchard-cli -- validate --resolve podman-desktop
cargo run --manifest-path orchard/Cargo.toml -p orchard-cli -- validate --resolve nomachine
```

Expected: each command resolves a valid final download URL.

- [ ] **Step: Commit verification fixes**

If verification changes files, commit them:

```bash
git add orchard home/dot_config/orchard home/dot_config/fish/completions/orchard.fish
git commit -m "fix: Polish Orchard Rust migration"
```

## Acceptance Criteria

- Rust workspace builds with `cargo check`.
- All Rust tests pass.
- `cargo clippy` passes with warnings denied.
- `orchard validate` works against KDL manifests.
- `orchard validate --resolve` works for representative direct, GitHub,
  JSON, HTML, XML, and Sparkle packages.
- KDL manifests keep `bundle`, `fetch`, `download`, `install`, `bin`, and
  `action` inside `platform "macos"`.
- Install scheduling has tests showing fetch and download can be modeled
  concurrently while install and side effects remain serialized.
- Every existing Fish package has a KDL manifest equivalent.
- No KDL manifest contains shell snippets, arbitrary commands, or callback
  code.
- Markdown documentation passes markdownlint.
