#!/usr/bin/env fish

function codex --description 'Ensure Codex is installed, then run codex with given arguments'
    __ensure_binary_and_forward \
        --bin "$HOME/.local/bin/codex" \
        --name Codex \
        --install __codex_install \
        -- $argv
end

function __codex_install --description 'internal: install Codex'
    curl -fsSL https://chatgpt.com/codex/install.sh | sh
end
