#!/usr/bin/env fish

function apm-add-skill --description "Add skill packages to APM source config, install, and chezmoi add"
    set -l usage "\
Usage: apm-add-skill [--global] <package> [<package> ...]
  default: add packages to the local custom source
  --global: add packages to the tracked base source
  github.com/owner/repo/path/to/skill
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
    __apm-add-to-source $add_args; or return $status

    __apm-merge-source-config; or begin
        set -l merge_status $status
        __apm-remove-dependencies "$source_path" $pkgs
        __apm-merge-source-config
        return $merge_status
    end

    __apm-run-global-apm install; or begin
        set -l install_status $status
        __apm-remove-dependencies "$source_path" $pkgs
        __apm-merge-source-config
        return $install_status
    end

    __apm-link-skills-to-agents; or begin
        set -l link_status $status
        __apm-remove-dependencies "$source_path" $pkgs
        __apm-merge-source-config
        return $link_status
    end

    set -l target_path "$__apm_home/"(path basename "$source_path")
    command cp -f "$source_path" "$target_path"; or return 1
    chezmoi add "$target_path"
end
