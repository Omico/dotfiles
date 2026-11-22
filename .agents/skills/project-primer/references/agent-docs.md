# Agent Docs

Read this before editing `.agents/`, `docs/`, `docs/scripts/generate-docs.mjs`, `docs/scripts/markdownlint.mjs`, or the docs CI workflow.

## Contract

- Root `AGENTS.md` stays minimal and routes to `project-primer`.
- Follow [markdown](markdown.md) for human-facing repository documentation placement and formatting.
- `docs/scripts/generate-docs.mjs` emits VitePress pages from `.agents/skills/`.
- `docs/scripts/markdownlint.mjs` lints repository Markdown via markdownlint-cli2 and enforces the no-hard-wrap rule from [markdown](markdown.md).
- Do not hand-edit generated VitePress sidebar files (`sidebar.generated.mts`, `nav.generated.mts`).
- Commands docs under `docs/src/commands/` are hand-maintained; when Fish autoload commands change, see [commands-docs](commands-docs.md).
- Use the `vitepress` skill for detailed guidance when working with VitePress. Follow this reference and the existing docs scripts for the repository workflow.

## Verification

- Run `npm run docs:build` in `docs/` after changing `.agents/`, `docs/`, the docs generator, or docs workflow.
- CI workflow: `.github/workflows/docs.yml` (`Deploy docs`).
