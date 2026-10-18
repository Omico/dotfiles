#!/usr/bin/env fish

set -g __apm_home "$HOME/.apm"
set -g __apm_yq_merge_expr '
  select(fileIndex == 0) as $base |
  select(fileIndex == 1) as $environment |
  select(fileIndex == 2) as $custom |
  $base |
  .dependencies.apm = ((($base.dependencies.apm // []) + ($environment.dependencies.apm // []) + ($custom.dependencies.apm // [])) | unique | sort) |
  .dependencies.mcp = ((($base.dependencies.mcp // []) + ($environment.dependencies.mcp // []) + ($custom.dependencies.mcp // [])))
'

function __apm-run-global-apm
    pushd "$__apm_home"
    apm $argv
    set -l apm_status $status
    popd
    return $apm_status
end

function __apm-require-yq
    command -q yq; or begin
        echo "Error: yq is required to merge APM source config." >&2
        return 1
    end
end

function __apm-require-source-paths
    set -l source_dir (chezmoi source-path 2>/dev/null)/dot_apm
    test -d "$source_dir"; or set source_dir "$HOME/.local/share/chezmoi/home/dot_apm"

    set -l base_path "$source_dir/apm.base.yml"
    test -e "$base_path"; or begin
        printf "Error: base source not found: %s\n" "$base_path" >&2
        return 1
    end

    set -l environment
    if test -e "$source_dir/apm.environment"
        set environment (string trim <"$source_dir/apm.environment")
    else
        if command -q gh
            set -l login (gh api --hostname github.com user --jq .login 2>/dev/null)
            set -l login_status $status
            if test $login_status -eq 0; and test (count $login) -eq 1; and string match -rq '^[A-Za-z0-9][A-Za-z0-9-]*$' -- "$login"
                if string match -qi Omico -- "$login"
                    set environment internal
                else
                    set environment external
                end
            end
        end
        if test -z "$environment"
            if not isatty stdin
                printf "Error: select external or internal in %s/apm.environment before running without terminal input.\n" "$source_dir" >&2
                return 1
            end
            printf 'Select the skill environment:\n1. external — Public external skills\n2. internal — Vita + Omico Skills\n' >&2
            while true
                printf 'Selection: ' >&2
                read --local --prompt-str '' selection; or return 1
                switch "$selection"
                    case 1 external
                        set environment external
                    case 2 internal
                        set environment internal
                    case '*'
                        echo 'Enter 1 (external) or 2 (internal).' >&2
                        continue
                end
                break
            end
        end
        printf '%s\n' "$environment" >"$source_dir/apm.environment"; or return 1
    end
    if not contains -- "$environment" external internal
        echo "Error: apm.environment must contain external or internal." >&2
        return 1
    end
    set -l custom_path "$source_dir/apm.custom.yml"
    set -l environment_path "$source_dir/apm.$environment.yml"

    test -f "$environment_path"; or begin
        printf "Error: environment source not found: %s\n" "$environment_path" >&2
        return 1
    end

    echo "$base_path"
    echo "$custom_path"
    echo "$environment_path"
end

function __apm-ensure-custom-source --argument-names custom_path
    if test -e "$custom_path"
        return 0
    end

    command mkdir -p (path dirname "$custom_path"); or return 1
    printf 'dependencies:\n  apm: []\n' >"$custom_path"; or return 1
end

function __apm-add-dependencies --argument-names source_path
    set -l additions $argv[2..-1]
    test (count $additions) -gt 0; or return 0

    if not test -e "$source_path"
        __apm-ensure-custom-source "$source_path"; or return 1
    end

    set -l quoted (string join '", "' $additions)
    yq -i ".dependencies.apm += [\"$quoted\"] | .dependencies.apm |= (unique | sort)" "$source_path"
    or return 1
end

function __apm-merge-source-config
    __apm-require-yq; or return $status

    set -l paths (__apm-require-source-paths); or return $status
    set -l base_path $paths[1]
    set -l custom_path $paths[2]
    set -l environment_path $paths[3]
    set -l output_path "$__apm_home/apm.yml"

    command mkdir -p "$__apm_home"; or return 1

    __apm-ensure-custom-source "$custom_path"; or return $status
    # Snap yq can read non-hidden paths under HOME.
    set -l temporary_dir (command mktemp -d "$HOME/apm-merge.XXXXXXXXXX"); or return 1
    command cp "$base_path" "$temporary_dir/apm.base.yml"
    and command cp "$environment_path" "$temporary_dir/apm.environment.yml"
    and command cp "$custom_path" "$temporary_dir/apm.custom.yml"
    and yq eval-all "$__apm_yq_merge_expr" "$temporary_dir/apm.base.yml" "$temporary_dir/apm.environment.yml" "$temporary_dir/apm.custom.yml" >"$temporary_dir/apm.yml"
    or begin
        command rm -rf "$temporary_dir"
        return 1
    end
    command mv "$temporary_dir/apm.yml" "$output_path"
    set -l move_status $status
    command rm -rf "$temporary_dir"; or return 1
    return $move_status
end

function __apm-link-skills-to-agents
    set -l apm_skills "$__apm_home/.agents/skills"
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

    # Migrate from linking the whole skills directory to per-skill symlinks.
    if test -L "$agents_skills"
        command rm "$agents_skills"
        or begin
            echo "Error: failed to remove directory symlink $agents_skills." >&2
            return 1
        end
    end

    if test -e "$agents_skills"; and not test -d "$agents_skills"
        echo "Error: $agents_skills exists and is not a directory." >&2
        return 1
    end

    command mkdir -p "$agents_skills"
    or begin
        echo "Error: failed to create $agents_skills." >&2
        return 1
    end

    for entry in $agents_skills/*
        set -l name (path basename $entry)
        if test -L $entry
            set -l target (readlink $entry)
            if string match -q -- "$apm_skills/*" $target
                if not test -e "$apm_skills/$name"
                    command rm -f $entry
                    or return 1
                end
            end
        end
    end

    for skill_dir in $apm_skills/*
        test -d $skill_dir; or continue
        test -L $skill_dir; and continue

        set -l name (path basename $skill_dir)
        set -l dest "$agents_skills/$name"

        # Preserve links owned by plugins or other local installers.
        if test -L $dest
            if test (readlink $dest) != "$skill_dir"
                printf "Keeping existing skill link: %s\n" $dest
            end
            continue
        end

        if test -e $dest
            printf "Error: %s exists and is not a symlink.\n" $dest >&2
            return 1
        end

        command ln -sfn $skill_dir $dest
        or begin
            printf "Error: failed to link %s.\n" $dest >&2
            return 1
        end
    end
end

function __apm-normalize-skill-refs
    set -l pkgs
    for ref in $argv
        # https://github.com/<owner>/<repo>/blob/<branch>/<path[/SKILL.md]> -> <owner>/<repo>/<path>
        set -l m (string match -r '^https?://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)$' "$ref")
        if test (count $m) -ge 5
            set -l owner $m[2]
            set -l repo $m[3]
            set -l relpath $m[5]
            set -l relpath (string replace -r '(^|/)SKILL\.md$' '' "$relpath")
            set -l relpath (string replace -r '/$' '' "$relpath")
            set ref "$owner/$repo"
            if test -n "$relpath"
                set ref "$ref/$relpath"
            end
        end
        set -a pkgs (string replace -r '^github\.com/' '' "$ref")
    end
    printf "%s\n" $pkgs
end

function __apm-add-to-source
    set -l use_global false
    if test "$argv[1]" = --global
        set use_global true
        set argv $argv[2..-1]
    end

    set -l pkgs $argv
    test (count $pkgs) -gt 0; or return 0

    __apm-require-yq; or return $status

    set -l paths (__apm-require-source-paths); or return $status
    set -l base_path $paths[1]
    set -l custom_path $paths[2]

    set -l target_path $custom_path
    if test "$use_global" = true
        set target_path $base_path
    else
        __apm-ensure-custom-source "$custom_path"; or return $status
    end

    __apm-add-dependencies "$target_path" $pkgs
end
