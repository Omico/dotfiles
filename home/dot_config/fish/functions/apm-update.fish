#!/usr/bin/env fish

function apm-update --description "Update agent skills via APM (apm deps update in ~/.apm)"
    echo "Updating agent skills from ~/.apm..."

    __apm-run-global-apm update; or return $status
    __apm-run-global-apm deps update --parallel-downloads 32 $argv; or return $status

    __link-apm-skills-to-agents
end
