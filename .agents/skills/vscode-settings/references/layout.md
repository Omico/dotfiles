# Layout and apply

Read when choosing source paths, ignored-file shape, merge semantics, or **Push** into live settings.

## Source paths

Chezmoi source → destination:

| Source | Destination |
| --- | --- |
| `home/dot_config/vscode-settings/shared.json` | `~/.config/vscode-settings/shared.json` |
| `home/dot_config/vscode-settings/code.json` | `~/.config/vscode-settings/code.json` |
| `home/dot_config/vscode-settings/cursor.json` | `~/.config/vscode-settings/cursor.json` |
| `home/dot_config/vscode-settings/ignored.json` | `~/.config/vscode-settings/ignored.json` |
| `home/dot_config/vscode-settings/code.ignored.json` | `~/.config/vscode-settings/code.ignored.json` |
| `home/dot_config/vscode-settings/cursor.ignored.json` | `~/.config/vscode-settings/cursor.ignored.json` |

Ignored files are JSON arrays of top-level setting key strings. Missing ignored files mean `[]`.

## Apply pipeline

**Push** path — `vscode-settings-apply` (Unix Fish function):

1. `managed = shallow_override(shared, app_unique)`; a missing app layer is `{}`
2. Drop keys from `ignored.json ∪ <app>.ignored.json`
3. `out = shallow_override(live, managed′)`; managed top-level values replace live values completely, while ignored keys keep live values

The command accepts full JSONC in existing live settings and prepares both outputs before replacing either live file. Missing live files start from `{}`, but an existing empty or comment-only file is invalid because it contains no root document. A parse or merge failure leaves both applications unchanged. Managed and ignored layer files remain strict JSON; optional files may be missing, but an existing non-regular path is an error.

Push depends on Fish, `iconv`, and `jq` 1.7 or newer with literal-number preservation. Startup verifies the required `jq` behavior. Fish validates UTF-8 and rejects raw NUL bytes before capturing file content; its normalizer then removes JSONC comments and trailing commas without touching string content, rejects non-standard or out-of-range JSON numbers, and lets `jq` validate one root document and perform shallow map operations without routing JSON through YAML semantics.

Pull's Python parser remains package-local at `.agents/skills/vscode-settings/scripts/vscode_settings_jsonc.py` so the skill is standalone.

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
