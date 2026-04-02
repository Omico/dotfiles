#!/usr/bin/env fish

function rustup --description 'Ensure rustup is installed, then run rustup with given arguments'
    set -l bin "$HOME/.cargo/bin/rustup"
    if not test -x "$bin"
        printf "rustup not found; installing via rustup.rs...\n" >&2
        curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
        or begin
            printf "rustup installation failed.\n" >&2
            return 1
        end
    end
    command "$bin" $argv
end
