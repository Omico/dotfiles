# Implementation Phase 4: CLI, Migration, and Docs

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this phase task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose the Rust implementation through the CLI, migrate current Fish packages to KDL, and update shell integration plus docs.

**Architecture:** `orchard-cli` orchestrates core, fetch, and macOS crates. `orchard-migrate` provides conversion helpers while all package behavior lands under `platform "macos"`.

**Tech Stack:** Rust, `clap`, fixture manifests, Fish completions, Markdown.

---

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

Respect `XDG_CONFIG_HOME` and `XDG_CACHE_HOME`, defaulting to `~/.config/orchard` and `~/.cache/orchard`.

- [ ] **Step: Implement `list`**

Load KDL manifests, compute installed state through `orchard-macos`, and print the app ID with installed status and version when available.

- [ ] **Step: Implement `validate`**

Run static validation by default. With `--resolve`, run fetch resolution for the current host platform and architecture. With `--all-platforms`, parse and validate all platform blocks that have implemented schema rules.

- [ ] **Step: Implement `install`**

Load, validate, select `platform "macos"`, resolve, download, install, and run declared side effects through the staged scheduler. Honor `--force` when the app is already installed.

- [ ] **Step: Implement `cleanup`**

Remove the Orchard cache directory and report the cleared path.

- [ ] **Step: Add CLI integration tests**

Use temporary XDG directories and fixture manifests to test `validate` and `list` without network or privileged commands.

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

`orchard-migrate` should parse common Fish variable assignments and emit KDL drafts for direct packages. Dynamic packages should be matched by known package ID and converted through explicit Rust mapping code. All generated behavior must be nested under `platform "macos"`.

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

Completions should read `*.kdl` app IDs and include `--resolve` and `--all-platforms` for `validate`.

- [ ] **Step: Add README**

`orchard/README.md` should explain how to build, validate, and install with the Rust CLI.

- [ ] **Step: Update design doc with final parser choice**

Record the official `kdl` crate as the schema parser and confirm that schema v1 uses top-level app identity plus nested platform blocks.

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
