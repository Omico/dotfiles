# Implementation Phase 5: Final Verification

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this phase task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Verify the Rust Orchard migration is complete and the docs remain lint-clean.

**Architecture:** This phase runs full-workspace checks and representative package resolution tests after all implementation and migration work is in place.

**Tech Stack:** Cargo, clippy, Rust tests, Orchard CLI, markdownlint.

---

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
- `orchard validate --resolve` works for representative direct, GitHub, JSON, HTML, XML, and Sparkle packages.
- KDL manifests keep `bundle`, `fetch`, `download`, `install`, `bin`, and `action` inside `platform "macos"`.
- Install scheduling has tests showing fetch and download can be modeled concurrently while install and side effects remain serialized.
- Every existing Fish package has a KDL manifest equivalent.
- No KDL manifest contains shell snippets, arbitrary commands, or callback code.
- Markdown documentation passes markdownlint.
