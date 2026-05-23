# Markdown

Read this before editing Markdown files, skill files, repository docs, or long Markdown-like comments.

## Structure

- Use descriptive headings, not numbered headings.
- Avoid hard-coded section numbers in overviews and cross-references.
- Prefer unordered bullets with bold labels over ordered lists in prose.
- Refer to sections by name, not number.
- Keep headings stable enough that links remain meaningful after reordering.
- Do not hard-wrap Markdown prose or list items; keep each logical paragraph or bullet on one physical line unless Markdown syntax requires a line break.

## Comments and strings

- Mirror this structure in long code comments and script-generated Markdown.
- Keep repository text in English; follow [english-only](english-only.md).

## Verification

- Run `bash scripts/markdownlint.sh` from the repository root for Markdown checks.
- Run `bash scripts/markdownlint.sh --fix` from the repository root to apply markdownlint-cli2 built-in fixes.
- Fix every reported issue before considering the Markdown change complete.
