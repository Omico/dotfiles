#!/usr/bin/env fish

function apm --description "APM CLI; installs via https://aka.ms/apm-unix if missing"
    __ensure_binary_and_forward /usr/local/bin/apm apm sh \
        "curl -sSL https://aka.ms/apm-unix | sh" \
        $argv
end
