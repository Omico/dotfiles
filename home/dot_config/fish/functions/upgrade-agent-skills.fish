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
        printf "upgrade-agent-skills: no install entries or invalid JSON in %s\n" "$skills_file" >&2
        return 1
    end

    set -l total (count $entries)
    set -l label (test $total -eq 1; and echo "entry"; or echo "entries")
    echo "Upgrading agent skills ($total $label)..."

    set -l n 0
    for entry in $entries
        set n (math "$n + 1")

        set -l source (echo "$entry" | jq -r '.source // empty')
        if test -z "$source"
            printf "[%d/%d] skip (no source)\n" $n $total >&2
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

        printf "[%d/%d] %s\n" $n $total "$source"
        if not $cmd
            printf "upgrade-agent-skills: failed at entry %d (%s)\n" $n "$source" >&2
            return 1
        end
    end

    echo "Done. Upgraded $total $label."
end
