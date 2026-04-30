# Implementation Phase 2: Fetch Engine

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this phase task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve final download URLs from selected platform manifests.

**Architecture:** `orchard-fetch` depends on `orchard-core` and implements direct URLs, GitHub release asset selection, selector extraction, and template interpolation without privileged host operations.

**Tech Stack:** Rust, `reqwest`, `serde_json`, `regex`, fixture tests.

---

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

Fetch latest release JSON, choose the first matching asset regex for the host architecture, and return `browser_download_url`.

- [ ] **Step: Implement pipeline requests and selectors**

Support:

- `format="json"` with `json` and `json-key="max-numeric"`.
- `format="text"` with `regex`.
- `format="xml"` with `xml-text`.
- `format="sparkle"` with `sparkle-enclosure-contains`.

- [ ] **Step: Implement template interpolation**

Templates may use `{host.arch}`, `let` variables, and extracted variables. Missing variables produce typed errors.

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
