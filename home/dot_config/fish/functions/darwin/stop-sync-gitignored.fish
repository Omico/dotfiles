#!/usr/bin/env fish

function stop-sync-gitignored --description "Mark gitignored paths with the File Provider ignore xattr"
    for dependency in git xattr
        type -q $dependency; or begin
            echo "$dependency command not found." >&2
            return 1
        end
    end

    set -l usage "Usage: stop-sync-gitignored [--dry-run] [path]"

    argparse h/help n/dry-run -- $argv
    set -l argparse_status $status

    set -q _flag_help; and begin
        echo $usage
        echo "Mark ignored paths with com.apple.fileprovider.ignore#P."
        return 0
    end

    test $argparse_status -eq 0 -a (count $argv) -le 1; or begin
        echo $usage >&2
        return 1
    end

    set -l repo_hint .
    set -q argv[1]; and set repo_hint $argv[1]

    if not test -e "$repo_hint"
        echo "Path not found: $repo_hint" >&2
        return 1
    end

    set -l repo_path "$repo_hint"
    test -f "$repo_path"; and set repo_path (dirname "$repo_path")

    set -l repo_root (command git -C "$repo_path" rev-parse --show-toplevel 2>/dev/null)
    if test -z "$repo_root"
        echo "Not inside a git repository: $repo_hint" >&2
        return 1
    end

    set -l ignored_paths (
        command git -C "$repo_root" status --ignored --porcelain=v1 -z \
        | string split0 \
        | string match -r '^!! .+' \
        | string replace -r '^!! ' '' \
        | string replace -r '/$' ''
    )

    if not set -q ignored_paths[1]
        echo "No ignored paths found in $repo_root"
        return 0
    end

    if set -q _flag_dry_run
        for rel_path in $ignored_paths
            echo "Would mark: $rel_path"
        end
        echo "Found "(count $ignored_paths)" ignored path(s) in $repo_root."
        return 0
    end

    set -l failed_count 0

    for rel_path in $ignored_paths
        if command xattr -w 'com.apple.fileprovider.ignore#P' 1 "$repo_root/$rel_path"
            echo "Marked: $rel_path"
            continue
        else
            echo "Failed: $rel_path" >&2
            set failed_count (math "$failed_count + 1")
        end
    end

    set -l marked_count (math (count $ignored_paths) - $failed_count)
    echo "Marked $marked_count ignored path(s) in $repo_root."

    if test $failed_count -gt 0
        echo "Failed to mark $failed_count path(s)." >&2
        return 1
    end
end
