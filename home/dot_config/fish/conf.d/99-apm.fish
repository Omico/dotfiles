#!/usr/bin/env fish

function __apm-run-global-apm
    pushd "$HOME/.apm"
    apm $argv
    set -l apm_status $status
    popd
    return $apm_status
end

function __link-apm-skills-to-agents
    set -l apm_skills "$HOME/.apm/.agents/skills"
    set -l agents_root "$HOME/.agents"
    set -l agents_skills "$agents_root/skills"

    if not test -d "$apm_skills"
        echo "Error: $apm_skills not found." >&2
        return 1
    end

    command mkdir -p "$agents_root"
    or begin
        echo "Error: failed to create $agents_root." >&2
        return 1
    end

    if test -e "$agents_skills"; and not test -L "$agents_skills"
        echo "Error: $agents_skills exists and is not a symlink." >&2
        return 1
    end

    command ln -sf "$apm_skills" "$agents_skills"
    or begin
        echo "Error: failed to link $agents_skills." >&2
        return 1
    end
end

function __apm-normalize-skill-ref --argument-names ref
    # https://github.com/<owner>/<repo>/blob/<branch>/<path[/SKILL.md]> -> github.com/<owner>/<repo>/<path>
    set -l m (string match -r '^https?://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)$' "$ref")
    if test (count $m) -ge 5
        set -l owner $m[2]
        set -l repo $m[3]
        set -l relpath $m[5]
        set -l relpath (string replace -r '/SKILL\.md$' '' "$relpath")
        set -l relpath (string replace -r '/$' '' "$relpath")
        echo "github.com/$owner/$repo/$relpath"
        return 0
    end

    echo "$ref"
end
