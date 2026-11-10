#!/usr/bin/env fish

function rustup --description 'Ensure rustup is installed, then run rustup with given arguments'
    __ensure_binary_and_forward \
        --bin "$HOME/.cargo/bin/rustup" \
        --name rustup \
        --install __rustup_install \
        -- $argv
end

function __rustup_install --description 'internal: install rustup'
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
end
