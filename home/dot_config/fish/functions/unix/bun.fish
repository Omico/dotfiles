#!/usr/bin/env fish

function bun --description 'Ensure bun is installed, then run bun with given arguments'
    __ensure_binary_and_forward "$HOME/.bun/bin/bun" Bun bash \
        "curl -fsSL https://bun.sh/install | bash" $argv
end
