# Implementation Phase 1: Foundation and Schema

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this phase task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the Rust workspace and implement typed KDL manifest parsing and static validation.

**Architecture:** This phase establishes the workspace and `orchard-core`, which owns manifest structs, platform blocks, parsing, and validation.

**Tech Stack:** Rust, Cargo workspace, official `kdl` crate, `thiserror`, and unit tests.

---

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

`orchard-cli` depends on `orchard-core`, `orchard-fetch`, and `orchard-macos`. `orchard-fetch` depends on `orchard-core`. `orchard-migrate` depends on `orchard-core`.

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

Create enums and structs for `PlatformId`, `PlatformManifest`, `DownloadFormat`, `InstallOperation`, `Fetch`, `FetchStep`, `Bin`, `Action`, `Bundle`, and `InstalledState`.

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

Parse `app "<id>" schema=1 { ... }` using `kdl::KdlDocument`, parse nested `platform "<id>" { ... }` blocks, then convert nodes into the typed model. Return a typed parse error that includes the manifest path and field name.

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
- Top-level app nodes do not contain platform-only nodes such as `bundle`, `fetch`, `download`, `install`, `bin`, or `action`.
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
