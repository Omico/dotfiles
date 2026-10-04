#!/usr/bin/env fish

function uv --description 'Ensure uv is installed, then run uv with given arguments'
    __ensure_binary_and_forward \
        --bin "$HOME/.local/bin/uv" \
        --name uv \
        --install __uv_install \
        -- $argv
end

function __uv_install --description 'internal: install uv'
    curl -LsSf https://astral.sh/uv/install.sh | sh
end
