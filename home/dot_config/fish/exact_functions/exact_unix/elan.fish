#!/usr/bin/env fish

function elan --description 'Ensure elan is installed, then run elan with given arguments'
    __ensure_binary_and_forward \
        --bin "$HOME/.elan/bin/elan" \
        --name elan \
        --install __elan_install \
        -- $argv
end

function __elan_install --description 'internal: install elan'
    curl -sSf https://elan.lean-lang.org/elan-init.sh | sh -s -- -y --no-modify-path
    or return

    fish_add_path "$HOME/.elan/bin"
    or return 0
end
