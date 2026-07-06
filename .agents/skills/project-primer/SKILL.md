---
name: project-primer
description: Use before exploring or changing this chezmoi repository. Routes to the smallest local reference for stored text, Markdown, docs, Fish scripts, Orchard, APM, or commits.
---

# Project Primer

Repository rule router. Load first, then open only the focused references needed for the task.

## Use

- Read the route table and choose the smallest matching reference.

## Stop Rule

Stop when the current reference gives enough guidance. Load another reference only when the task crosses surfaces.

## Routes

- **Stored text**: Read [english-only](references/english-only.md) before editing non-Markdown comments, descriptions, command output, or user-facing strings.
- **Markdown**: Read [markdown](references/markdown.md) before editing `.md` files, skills, docs, or Markdown-like comments.
- **Agent docs**: Read [agent-docs](references/agent-docs.md) before editing `.agents/`, `docs/`, the docs generator, or docs CI.
- **Scripts and local commands**: Read [fish](references/fish.md) before creating, moving, or editing shell scripts, local commands, Fish functions, Fish completions, Fish-based local executables, or platform-specific helpers.
- **Commands docs**: Read [commands-docs](references/commands-docs.md) when adding, renaming, or removing Fish autoload commands or editing `docs/src/commands/`.
- **Orchard**: Read [orchard](references/orchard.md) before editing Orchard app packages, its executable, or its completion.
- **APM**: Read [apm](references/apm.md) before editing APM source under `home/dot_apm/` or APM Fish helpers.
- **Commits**: Read [git](references/git.md) before preparing a commit.
