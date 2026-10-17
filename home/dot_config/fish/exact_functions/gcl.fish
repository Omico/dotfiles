#!/usr/bin/env fish

# Configure host-specific clone roots with host/base-dir pairs:
# set -g gcl_remote_host_base_dirs \
#     gitlab.com "$HOME/GitLab" \
#     git.company.com "$HOME/Work/GitLab"
#
# Matching hosts clone to the configured base dir while preserving the remote path.
# Unmatched hosts clone to $HOME/Git/<remote-path>.
function gcl --description 'Clone a git repository using its remote path'
    if not command -q git
        printf "Git command not found.\n" >&2
        return 1
    end

    if test (count $argv) -eq 0
        printf "Usage: gcl <repository> [git-clone-args...]\n" >&2
        return 1
    end

    set -l git_dir "$HOME/Git"
    set -l repository $argv[1]
    set -l clone_args $argv[2..-1]

    set -l repository_info (__gcl_parse_repository "$repository"); or return 1
    set -l remote_host $repository_info[1]
    set -l repository_path $repository_info[2]

    set -l target_base_dir (__gcl_target_base_dir "$git_dir" "$remote_host"); or return 1

    set -l target_dir "$target_base_dir/$repository_path"
    mkdir -p (dirname "$target_dir"); or return 1

    git clone $clone_args "$repository" "$target_dir"
end

function __gcl_parse_repository --argument-names repository
    set -l remote_path (__gcl_normalize_repository_path "$repository")
    set -l remote_parts (string split / -- $remote_path)

    if test (count $remote_parts) -lt 2
        printf "Unable to parse repository path: %s\n" "$repository" >&2
        return 1
    end

    printf "%s\n%s\n" "$remote_parts[1]" (string join / -- $remote_parts[2..-1])
end

function __gcl_normalize_repository_path --argument-names repository
    set -l remote_path $repository

    if string match -q -r '^[A-Za-z][A-Za-z0-9+.-]*://' -- $remote_path
        set remote_path (string replace -r '^[A-Za-z][A-Za-z0-9+.-]*://([^/]+)/' '$1/' -- $remote_path)
        set remote_path (string replace -r '^[^/@]+@' '' -- $remote_path)
        set remote_path (string replace -r '^([^/:]+):[0-9]+/' '$1/' -- $remote_path)
    else
        set remote_path (string replace -r '^[^@:/]+@([^:]+):' '$1/' -- $remote_path)
    end

    set remote_path (string replace -r '/+$' '' -- $remote_path)
    string replace -r '\.git$' '' -- $remote_path
end

function __gcl_target_base_dir --argument-names git_dir remote_host
    set -l target_base_dir "$git_dir"

    if not set -q gcl_remote_host_base_dirs
        printf "%s\n" "$target_base_dir"
        return 0
    end

    set -l override_count (count $gcl_remote_host_base_dirs)
    if test $override_count -eq 0
        printf "%s\n" "$target_base_dir"
        return 0
    end

    if test (math $override_count % 2) -ne 0
        printf "gcl_remote_host_base_dirs must contain host/base-dir pairs.\n" >&2
        return 1
    end

    for index in (seq 1 2 $override_count)
        set -l override_host $gcl_remote_host_base_dirs[$index]
        set -l override_path $gcl_remote_host_base_dirs[(math $index + 1)]

        if test "$remote_host" = "$override_host"
            set target_base_dir "$override_path"
            break
        end
    end

    printf "%s\n" "$target_base_dir"
end
