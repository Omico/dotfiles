#!/usr/bin/env fish

function upgrade-agent-skills --description "Upgrade agent skills from skills.json"
    set -l skills_file $argv[1]
    if test -z "$skills_file"
        set skills_file "$HOME/.local/share/chezmoi/skills.json"
    end

    if not test -f "$skills_file"
        echo "Error: skills file '$skills_file' not found." >&2
        return 1
    end

    if not type -q jq
        echo "Error: jq command not found. It is required to parse JSON." >&2
        return 1
    end

    if not type -q npx
        echo "Error: npx command not found. It is required to install skills." >&2
        return 1
    end

    set -l entries (jq -c '(.defaults // {}) as $d | .install[]? | ($d * .)' "$skills_file" 2>/dev/null)
    if test -z "$entries"
        printf "skills-install: no install entries or invalid JSON in %s\n" "$skills_file" >&2
        return 1
    end

    set -l n 0
    for entry in $entries
        set n (math "$n + 1")

        set -l source (echo "$entry" | jq -r '.source // empty')
        if test -z "$source"
            printf "skills-install: entry %d has no source, skipping.\n" $n >&2
            continue
        end

        set -l cmd npx skills add "$source"

        set -l skills (echo "$entry" | jq -r '.skills[]? // empty')
        for s in $skills
            set cmd $cmd --skill "$s"
        end

        set -l agents (echo "$entry" | jq -r '.agents[]? // empty')
        for a in $agents
            set cmd $cmd --agent "$a"
        end

        set -l use_global (echo "$entry" | jq -r '.global // false')
        set -l use_yes (echo "$entry" | jq -r '.yes // false')

        if test "$use_global" = true
            set cmd $cmd --global
        end
        if test "$use_yes" = true
            set cmd $cmd --yes
        end

        printf "skills-install: running: %s\n" (string join -- " " $cmd) >&2
        if not $cmd
            printf "skills-install: command failed for entry %d.\n" $n >&2
            return 1
        end
    end

    echo "Done installing skills from $skills_file."
end
