# Implementation Phase 3: macOS Runtime and Scheduling

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this phase task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement macOS archive handling, installation operations, declared side effects, locks, and staged install scheduling.

**Architecture:** `orchard-macos` wraps host commands behind traits, while `orchard-core` models scheduling so future multi-app installs can run fetch and download work concurrently while keeping system mutation serialized.

**Tech Stack:** Rust, mockable command runner, macOS command wrappers, filesystem locks.

---

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

Use app ID, resolved URL hash, and download format to produce paths compatible with the current cache behavior.

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

Test that each operation emits the expected command sequence without touching the host filesystem.

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

The default policy allows concurrent preparation work in the model, but keeps the system mutation phase serialized:

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
- The default policy serializes install stages even when preparation jobs are greater than one.

- [ ] **Step: Wire single-app install through the scheduler**

The first CLI may still accept one app ID, but it should use the staged scheduler path. This avoids a second control flow when multi-app install is added later.

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
