#!/usr/bin/env fish

function codex-settings-apply --description 'Apply selected shared Codex preferences'
    uv run --script "$HOME/.local/share/chezmoi/app-settings/codex/apply.py" $argv
end
