# Agent Rules

Read this file first. It centralizes lightweight rule metadata so an agent can decide which canonical rule file to open next instead of loading every rule up front.

## How to use this index

- Start here when you need repository-specific agent guidance.
- Before `git commit` or when generating a commit message for this repository, open `git-commit.mdc` first. It overrides generic Conventional Commit tooling defaults (including lowercase-only descriptions).
- Open only the matching canonical `.mdc` file after checking the metadata below.
- Treat this file as metadata-only. Keep the normative instructions in the referenced `.mdc` files.
- The canonical rule content lives under `.agents/rules/`, including subdirectories, and is stored in `.mdc` files.
- If this index conflicts with a referenced `.mdc` file under `.agents/rules/`, including subdirectories, the `.mdc` file takes precedence.

## Rule Index

| Rule | Description | Globs | Always Apply | Read When |
| --- | --- | --- | --- | --- |
| `vitepress-agents-docs.mdc` | `This repo syncs .agents rules and skills into VitePress via generate-docs.mjs; follow the vitepress-cursor-docs skill for procedures` | `.agents/commands/**/*.md,.agents/rules/**/*.mdc,.agents/skills/**/*.md,.github/workflows/docs.yml,docs/**` | `false` | Changing `.agents` commands, rules, or skills trees; `docs/`; `generate-docs.mjs`; or the docs GitHub Actions workflow. |
| `english-only.mdc` | `All script and code content must be in English only` | `\` | `true` | Always applied; use when unsure whether non-English text is allowed in scripts, code comments, or docs. |
| `fish-formatting.mdc` | `Formatting conventions for all fish scripts in this repo` | `**/*.fish` | `false` | Editing any Fish shell script (`.fish`). |
| `fish-home-config.mdc` | `Ensure fish scripts under home/dot_config/fish start with the standard shebang` | `home/dot_config/fish/**/*.fish` | `false` | Editing Fish config or functions under `home/dot_config/fish/`. |
| `git-commit.mdc` | `Git commit messages — Conventional Commits with capitalized prose after colons; mandatory for all agents when writing commits` | `\` | `true` | Creating a git commit or choosing a conventional commit message. |
| `markdown.mdc` | `Markdown style and structure guidelines for this repo` | `**/*.md,**/*.mdc` | `false` | Editing Markdown docs, specs, or rule files (`.md` / `.mdc`). |
| `orchard.mdc` | `Orchard development and maintenance (macOS app manager in this chezmoi repo)` | `home/dot_config/orchard/apps/*.fish,home/dot_local/bin/executable_orchard,home/dot_config/fish/completions/orchard.fish` | `false` | Changing Orchard app packages, the `orchard` executable, or Fish completions for Orchard. |

### Column conventions

- **Globs**
  - Comma-separated glob patterns, aligned with the rule file frontmatter `globs` field when present.
  - If the rule has no path globs (frontmatter omits `globs` or leaves it empty), write `\` in this column. That means the rule is not path-scoped; use **Read When** to decide when to open it.

## Maintenance

- Add a short metadata entry here for every new rule under `.agents/rules/`.
- When a rule's frontmatter metadata changes, update `.agents/rules/AGENTS.md` in the same change.
- Keep the metadata here aligned with each rule's frontmatter, especially `description`, `globs`, and `alwaysApply`. When `globs` is absent or empty, set the Globs column to `\`.
- Keep this file concise so it remains useful for progressive disclosure.
