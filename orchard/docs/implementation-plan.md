# Orchard Rust and KDL Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Phase files use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Rust version of Orchard that uses declarative KDL manifests instead of executable Fish app packages.

**Architecture:** The implementation is split into small Rust crates: `orchard-cli`, `orchard-core`, `orchard-fetch`, `orchard-macos`, and `orchard-migrate`. KDL manifests follow the `app -> platform -> fetch -> download -> install` model described in [manifest-schema.md](manifest-schema.md). Runtime behavior is described in [architecture.md](architecture.md).

**Tech Stack:** Rust, Cargo workspace, `clap`, official `kdl` crate, `thiserror`, `miette`, `reqwest`, `serde_json`, `regex`, `tempfile`, and mockable process execution wrappers.

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
- A staged install coordinator with per-app, per-cache-entry, and global install locks.
- CLI commands matching the existing Fish surface.
- KDL manifests for all current Orchard packages.

The plan does not include a GUI, background updates, arbitrary package scripts, fully parallel system install phases, Linux or Windows install backends, or a general plugin system.

## Phases

- [Phase 1: Foundation and Schema](implementation-phase-1-foundation.md)
- [Phase 2: Fetch Engine](implementation-phase-2-fetch.md)
- [Phase 3: macOS Runtime and Scheduling](implementation-phase-3-macos-runtime.md)
- [Phase 4: CLI, Migration, and Docs](implementation-phase-4-cli-migration-docs.md)
- [Phase 5: Final Verification](implementation-phase-5-verification.md)

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

## Acceptance Criteria

- Rust workspace builds with `cargo check`.
- All Rust tests pass.
- `cargo clippy` passes with warnings denied.
- `orchard validate` works against KDL manifests.
- `orchard validate --resolve` works for representative direct, GitHub, JSON, HTML, XML, and Sparkle packages.
- KDL manifests keep `bundle`, `fetch`, `download`, `install`, `bin`, and `action` inside `platform "macos"`.
- Install scheduling has tests showing fetch and download can be modeled concurrently while install and side effects remain serialized.
- Every existing Fish package has a KDL manifest equivalent.
- No KDL manifest contains shell snippets, arbitrary commands, or callback code.
- Markdown documentation passes markdownlint.
