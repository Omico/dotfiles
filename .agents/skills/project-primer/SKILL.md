---
name: project-primer
description: Use before exploring or changing this repository. Routes agents to the smallest focused project rule for files, scripts, docs, skills, workflows, and commits.
---

# Project Primer

Use this as the repository rule router. Load it first, then open only the focused references needed for the task.

## Use

- Read the route table, choose the smallest matching reference, and stop there.
- Combine references only when the task crosses surfaces.
- Keep human-facing repository documentation under `docs/`.
- After editing any Markdown file, run `bash scripts/markdownlint.sh` from the repository root; use `bash scripts/markdownlint.sh --fix` to apply markdownlint-cli2 fixes.

## Routes

- **Stored text**: Read [english-only](references/english-only.md) before editing non-Markdown comments, descriptions, command output, or user-facing strings.
- **Markdown**: Read [markdown](references/markdown.md) before editing `.md` files, skills, docs, or Markdown-like comments.
- **Agent docs**: Read [agent-docs](references/agent-docs.md) before editing `.agents/`, `docs/`, the docs generator, or docs CI.
- **Fish**: Read [fish](references/fish.md) before editing `.fish` files, Fish completions, or Fish-based local executables.
- **Orchard**: Read [orchard](references/orchard.md) before editing Orchard app packages, its executable, or its completion.
- **APM**: Read [apm](references/apm.md) before editing `home/dot_apm/`, `home/dot_config/fish/conf.d/99-apm.fish`, `home/dot_config/fish/functions/apm-add-skill.fish`, or `home/dot_config/fish/functions/apm-update.fish`.
- **Commits**: Read [git](references/git.md) before preparing a commit.
