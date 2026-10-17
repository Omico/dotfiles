#!/usr/bin/env fish

function mise --description 'Ensure mise is installed, then run mise with given arguments'
    __ensure_binary_and_forward \
        --bin "$HOME/.local/bin/mise" \
        --name mise \
        --install __mise_install \
        -- $argv
end

function __mise_install --description 'internal: install mise and activate the current shell'
    curl -fsSL https://mise.run | sh; or return $status
    $argv[1] activate fish | source
end
