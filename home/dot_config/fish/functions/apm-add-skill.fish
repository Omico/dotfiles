#!/usr/bin/env fish

function apm-add-skill --description "Add agent skill packages via APM (apm install in ~/.apm)"
    if test (count $argv) -eq 0
        echo "Usage: apm-add-skill <package> [<package> ...]" >&2
        echo "  github.com/owner/repo/path/to/skill" >&2
        echo "  https://github.com/owner/repo/blob/<branch>/path/SKILL.md  (blob URLs are normalized)" >&2
        return 1
    end

    set -l pkgs
    for a in $argv
        set -l one (__apm-normalize-skill-ref "$a")
        set pkgs $pkgs $one
    end

    __apm-run-global-apm install $pkgs; or return $status

    __link-apm-skills-to-agents

    chezmoi add $HOME/.apm/apm.yml
end
