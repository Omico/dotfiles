#!/usr/bin/env fish

function apm-add-skill --description "Add skill packages to APM source config, install, and chezmoi add"
    set -l usage "\
Usage: apm-add-skill [--global] <package> [<package> ...]
  default: add packages to the local custom source
  --global: add packages to the tracked base source
  owner/repo/path/to/skill
  https://github.com/owner/repo/blob/<branch>/path/SKILL.md  (blob URLs are normalized)"

    argparse g/global h/help -- $argv
    or begin
        echo $usage >&2
        return 1
    end

    if set -q _flag_help
        echo $usage
        return 0
    end

    if test (count $argv) -eq 0
        echo $usage >&2
        return 1
    end

    set -l pkgs (__apm-normalize-skill-refs $argv)

    set -l paths (__apm-require-source-paths); or return $status
    set -l source_path $paths[2]
    set -q _flag_global; and set source_path $paths[1]

    set -l add_args $pkgs
    set -q _flag_global; and set add_args --global $pkgs
    set -l snapshot_dir (command mktemp -d "$HOME/apm-add.XXXXXXXXXX"); or return 1
    set -l config_paths "$source_path" "$__apm_home/apm.yml"
    for config_path in $config_paths
        if test -e "$config_path"
            command cp -p "$config_path" "$snapshot_dir/"(path basename "$config_path"); or begin
                command rm -rf "$snapshot_dir"
                return 1
            end
        end
    end

    __apm-add-to-source $add_args
    and __apm-merge-source-config
    and __apm-run-global-apm install
    and __apm-link-skills-to-agents
    set -l add_status $status
    if test $add_status -ne 0
        set -l restore_failed false
        for config_path in $config_paths
            set -l snapshot "$snapshot_dir/"(path basename "$config_path")
            if test -e "$snapshot"
                command cp -p "$snapshot" "$config_path"; or set restore_failed true
            else
                command rm -f "$config_path"; or set restore_failed true
            end
        end
        if test "$restore_failed" = true
            printf 'Error: configuration rollback failed; snapshots remain in %s.\n' "$snapshot_dir" >&2
        else
            command rm -rf "$snapshot_dir"
        end
        return $add_status
    end
    command rm -rf "$snapshot_dir"; or return 1

    set -l target_path "$__apm_home/"(path basename "$source_path")
    command cp -f "$source_path" "$target_path"; or return 1
    chezmoi add "$target_path"
end
