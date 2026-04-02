#!/usr/bin/env fish

function rustup --description 'Ensure rustup is installed, then run rustup with given arguments'
    __ensure_binary_and_forward "$HOME/.cargo/bin/rustup" rustup sh \
        "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y" $argv
end
