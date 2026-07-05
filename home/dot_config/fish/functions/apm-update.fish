#!/usr/bin/env fish

function apm-update --description "Update agent skills via APM (apm deps update in ~/.apm)"
    echo "Updating agent skills from ~/.apm..."
    __apm-merge-source-config; or return $status
    __apm-run-global-apm self-update; or return $status
    __apm-run-global-apm update --yes --parallel-downloads 32 $argv; or return $status
    __apm-link-skills-to-agents; or return $status
end
