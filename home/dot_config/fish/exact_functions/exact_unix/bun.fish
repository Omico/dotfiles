#!/usr/bin/env fish

function bun --description 'Ensure bun is installed, then run bun with given arguments'
    __ensure_binary_and_forward \
        --bin "$HOME/.bun/bin/bun" \
        --name Bun \
        --install __bun_install \
        -- $argv
end

function __bun_install --description 'internal: install bun'
    curl -fsSL https://bun.sh/install | bash
end
