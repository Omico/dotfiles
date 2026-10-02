# Layout and apply

Read when choosing source paths, ignored-file shape, merge semantics, or **Push** into live settings.

## Source paths

Settings layers stay in the repository. Commands read them directly; there is no chezmoi deployment step for these files.

| Repository source | Command input |
| --- | --- |
| `app-settings/vscode-based/shared.json` | `~/.local/share/chezmoi/app-settings/vscode-based/shared.json` |
| `app-settings/vscode-based/code.json` | `~/.local/share/chezmoi/app-settings/vscode-based/code.json` |
| `app-settings/vscode-based/cursor.json` | `~/.local/share/chezmoi/app-settings/vscode-based/cursor.json` |
| `app-settings/vscode-based/ignored.json` | `~/.local/share/chezmoi/app-settings/vscode-based/ignored.json` |
| `app-settings/vscode-based/code.ignored.json` | `~/.local/share/chezmoi/app-settings/vscode-based/code.ignored.json` |
| `app-settings/vscode-based/cursor.ignored.json` | `~/.local/share/chezmoi/app-settings/vscode-based/cursor.ignored.json` |

Ignored files are JSON arrays of top-level setting key strings. Missing ignored files mean `[]`.

## Apply pipeline

`vscode-settings-apply` always processes both Code and Cursor; it has no single-app selector. For a single-app Apply request, follow Select the scope in `SKILL.md` before invoking it. This restriction applies to live writes, not source edits.

**Push** path — `vscode-settings-apply` (Unix Fish function):

1. `managed = shallow_override(shared, app_unique)`; a missing app layer is `{}`
2. Drop keys from `ignored.json ∪ <app>.ignored.json`
3. `out = shallow_override(live, managed′)`; managed top-level values replace live values completely, while ignored keys keep live values

The command accepts full JSONC in existing live settings and prepares both outputs before replacing either live file. Missing live files start from `{}`, but an existing empty or comment-only file is invalid because it contains no root document. A parse or merge failure leaves both applications unchanged. Managed and ignored layer files remain strict JSON; optional files may be missing, but an existing non-regular path is an error.

Push depends on Fish, `iconv`, and `jq` 1.7 or newer with literal-number preservation. Startup verifies the required `jq` behavior. Fish validates UTF-8 and rejects raw NUL bytes before capturing file content; its normalizer then removes JSONC comments and trailing commas without touching string content, rejects non-standard or out-of-range JSON numbers, and lets `jq` validate one root document and perform shallow map operations without routing JSON through YAML semantics.

Pull's Python parser remains package-local at `.agents/skills/app-settings/scripts/jsonc.py` so the skill is standalone.

Live targets:

| Platform | Code | Cursor |
| --- | --- | --- |
| darwin | `~/Library/Application Support/Code/User/settings.json` | `~/Library/Application Support/Cursor/User/settings.json` |
| linux / wsl | `~/.config/Code/User/settings.json` | `~/.config/Cursor/User/settings.json` |

Hook: `home/run_after_apply.fish.tmpl` runs `vscode-settings-apply` on Unix when the function exists and propagates a failed apply status.

## Fish implementation layout

Keep Push self-contained in `vscode-settings-apply.fish`. The public function appears first as a small orchestration layer; private Fish-native helpers follow in runtime/platform, input parsing, merge preparation, and transactional-write sections. Python remains limited to the standalone Pull command and tests.

## Layer rules

- **shared**: same key and value in both live files (after ignore filtering)
- **code** / **cursor**: app-only keys, or differing values (each side keeps its value)
- **yaml.disableSchemaDetection** when values differ: put the longer list in **shared**
- Prefer brace globs when consolidating path lists (example: `**/{.github,.gitea,.forgejo}/workflows/*.{yml,yaml}`)

## Source edits

Edit only the requested settings. A single-app source edit can touch shared and app-specific layers to retain the other application's effective values. When removing a key from `shared.json`, keep an existing override for the other app, or move the shared value into its app layer if it previously inherited that value. Finish with the source diff; run Apply only when requested.

- **Ignore a key globally**: add it to `ignored.json` and delete it from every managed layer.
- **Ignore a key for one app**: add it to `<app>.ignored.json`, remove it from `shared.json` and that app's layer, and keep or move the other app's value into the other app's layer.
- **Manage a key**: put identical values in `shared.json`, or app-only values in `code.json` / `cursor.json`.

Global ignores must be absent from every managed layer. App ignores must be absent from shared and the ignored app's layer.
