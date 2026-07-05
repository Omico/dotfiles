# Agent Docs

Read this before editing `.agents/`, `docs/`, `docs/scripts/generate-docs.mjs`, `docs/scripts/markdownlint.mjs`, or the docs CI workflow.

## Contract

- Root `AGENTS.md` stays minimal and routes to `project-primer`.
- Human-facing repository docs live under `docs/`.
- `docs/scripts/generate-docs.mjs` emits VitePress pages from `.agents/skills/`.
- `docs/scripts/markdownlint.mjs` lints repository Markdown via markdownlint-cli2 and enforces the no-hard-wrap rule from [markdown](markdown.md).
- Do not hand-edit generated VitePress sidebar files.
- Use the `vitepress-cursor-docs` skill for detailed docs workflow guidance.
- If that skill is unavailable, follow this reference and the existing docs scripts.

Install that skill if needed:

```bash
npx skills add OmicoDev/skills --skill vitepress-cursor-docs
```

## Verification

- Run `npm run docs:build` in `docs/` after changing `.agents/`, `docs/`, the docs generator, or docs workflow.
- CI workflow: `.github/workflows/docs.yml` (`Deploy docs`).
