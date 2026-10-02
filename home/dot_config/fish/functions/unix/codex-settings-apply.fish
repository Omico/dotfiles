#!/usr/bin/env fish

function codex-settings-apply --description 'Apply selected shared Codex preferences'
    command -q uv; or begin
        echo 'Error: uv is required for the Codex TOML merge helper.' >&2
        return 1
    end
    command uv run --script "$HOME/.config/codex-settings/apply.py" $argv
end
