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

    if not type -q npx
        echo "Error: npx command not found. It is required to install skills." >&2
        return 1
    end

    if not type -q jq
        echo "Error: jq command not found. It is required to parse JSON." >&2
        return 1
    end

    set -l entries (jq -c '(.defaults // {}) as $d | .install[]? | ($d * .)' "$skills_file")
    if test -z "$entries"
        printf "upgrade-agent-skills: no install entries or invalid JSON in %s\n" "$skills_file" >&2
        return 1
    end

    set -l total (count $entries)
    set -l label (test $total -eq 1; and echo "entry"; or echo "entries")
    echo "Upgrading agent skills ($total $label)..."

    set -l n 0
    set -l failures
    for entry in $entries
        set n (math "$n + 1")

        set -l source (printf '%s\n' "$entry" | jq -r '.source // empty')
        if test -z "$source"
            printf "[%d/%d] skip (no source)\n" $n $total >&2
            continue
        end

        set -l cmd_base npx skills add "$source"
        set -l common_flags

        for s in (printf '%s\n' "$entry" | jq -r '.skills[]? // empty')
            set common_flags $common_flags --skill "$s"
        end

        for a in (printf '%s\n' "$entry" | jq -r '.agents[]? // empty')
            set common_flags $common_flags --agent "$a"
        end

        if test (printf '%s\n' "$entry" | jq -r '.global // false') = true
            set common_flags $common_flags --global
        end

        if test (printf '%s\n' "$entry" | jq -r '.yes // false') = true
            set common_flags $common_flags --yes
        end

        set -l cmd $cmd_base $common_flags
        printf "[%d/%d] %s\n" $n $total (string join ' ' -- $cmd)
        if not $cmd
            set failures $failures $source
            printf "upgrade-agent-skills: failed to install from %s\n" "$source" >&2
        end
    end

    set -l failure_count (count $failures)
    if test $failure_count -gt 0
        echo "Done. Failed to install $failure_count skill(s)."
        echo "Failed sources:"
        printf "%s\n" $failures >&2
        return 1
    end

    echo "Done. Upgraded $total $label."
end
