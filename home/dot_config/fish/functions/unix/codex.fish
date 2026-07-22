#!/usr/bin/env fish

function codex --description 'Ensure Codex is installed, then run codex with given arguments'
    __ensure_binary_and_forward "$HOME/.local/bin/codex" Codex sh \
        "curl -fsSL https://chatgpt.com/codex/install.sh | sh" $argv
end
