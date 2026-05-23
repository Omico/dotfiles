# Markdown

Read this before editing Markdown files, skill files, repository docs, or long
Markdown-like comments.

## Structure

- Use descriptive headings, not numbered headings.
- Avoid hard-coded section numbers in overviews and cross-references.
- Prefer unordered bullets with bold labels over ordered lists in prose.
- Refer to sections by name, not number.
- Keep headings stable enough that links remain meaningful after reordering.

## Comments and strings

- Mirror this structure in long code comments and script-generated Markdown.
- Keep repository text in English; follow [english-only](english-only.md).

## Verification

- Run `npx markdownlint-cli2` on changed Markdown files.
- Fix every reported issue before considering the Markdown change complete.
