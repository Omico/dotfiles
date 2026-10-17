#!/usr/bin/env fish

function apm --description "APM CLI; installs via https://aka.ms/apm-unix if missing"
    __ensure_binary_and_forward \
        --bin "$HOME/.local/bin/apm" \
        --name apm \
        --install __apm_install \
        -- $argv
end

function __apm_install --description 'internal: install APM'
    curl -sSL https://aka.ms/apm-unix | sh
    source "$HOME/.apm/shell/fish.fish"
end
