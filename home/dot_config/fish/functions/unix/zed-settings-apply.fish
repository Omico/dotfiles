#!/usr/bin/env fish

function zed-settings-apply --description 'Merge portable Zed settings into the live user settings'
    __zed_settings_load_merge_engine; or return 1
    __vscode_settings_check_runtime; or return 1
    __zed_settings_check_platform; or return 1

    set -l source_dir "$HOME/.config/zed"
    set -l shared_path "$source_dir/settings.shared.json"
    set -l ignored_path "$source_dir/settings.ignored.json"
    set -l live_path "$source_dir/settings.json"

    __zed_settings_require_regular_file "$shared_path" 'shared settings'; or return 1
    __zed_settings_require_regular_file "$ignored_path" 'ignored keys'; or return 1

    set -l tmp_path (__vscode_settings_prepare_output "$live_path")
    or return 1

    __vscode_settings_build_merged \
        "$shared_path" \
        "" \
        "$ignored_path" \
        "" \
        "$live_path" \
        "$tmp_path"
    or begin
        echo 'Error: failed to merge Zed settings.' >&2
        command rm -f "$tmp_path"
        return 1
    end

    __vscode_settings_write_targets "$tmp_path" "$live_path"
end

function zed-settings-pull --description 'Update portable Zed settings from the live user settings'
    set -l dry_run 0
    switch (count $argv)
        case 0
        case 1
            if test "$argv[1]" = --dry-run
                set dry_run 1
            else
                echo 'Usage: zed-settings-pull [--dry-run]' >&2
                return 1
            end
        case '*'
            echo 'Usage: zed-settings-pull [--dry-run]' >&2
            return 1
    end

    __zed_settings_load_merge_engine; or return 1
    __vscode_settings_check_runtime; or return 1
    __zed_settings_check_platform; or return 1

    command -q chezmoi; or begin
        echo 'Error: chezmoi is required to locate the Zed settings source.' >&2
        return 1
    end

    set -l source_dir "$HOME/.config/zed"
    set -l ignored_path "$source_dir/settings.ignored.json"
    set -l managed_path "$source_dir/settings.shared.json"
    set -l live_path "$source_dir/settings.json"

    __zed_settings_require_regular_file "$ignored_path" 'ignored keys'; or return 1
    __zed_settings_require_regular_file "$live_path" 'live settings'; or return 1

    set -l source_path (command chezmoi source-path "$managed_path")
    set -l status_source_path $status
    if test $status_source_path -ne 0; or test (count $source_path) -ne 1; or test -z "$source_path"
        printf 'Error: failed to resolve the chezmoi source for %s\n' "$managed_path" >&2
        return 1
    end
    __zed_settings_require_regular_file "$source_path" 'chezmoi source settings'; or return 1

    set -l tmp_path (__vscode_settings_prepare_output "$source_path")
    or return 1
    set -l work_dir (mktemp -d)
    or begin
        command rm -f "$tmp_path"
        return 1
    end

    set -l live_clean_path "$work_dir/live.json"
    set -l ignored_clean_path "$work_dir/ignored.json"

    __vscode_settings_load_live_json "$live_path" >"$live_clean_path"
    or begin
        command rm -f "$tmp_path"
        command rm -rf "$work_dir"
        return 1
    end

    __vscode_settings_load_ignored_keys "$ignored_path" "" >"$ignored_clean_path"
    or begin
        command rm -f "$tmp_path"
        command rm -rf "$work_dir"
        return 1
    end

    command jq --indent 2 --slurp \
        '.[0] as $live | .[1] as $ignored | reduce $ignored[] as $key ($live; del(.[$key]))' \
        "$live_clean_path" "$ignored_clean_path" >"$tmp_path"
    set -l status_jq $status
    command rm -rf "$work_dir"
    if test $status_jq -ne 0
        echo 'Error: failed to build portable Zed settings.' >&2
        command rm -f "$tmp_path"
        return 1
    end

    if test $dry_run -eq 1
        command diff -u "$source_path" "$tmp_path"
        set -l status_diff $status
        command rm -f "$tmp_path"
        if test $status_diff -gt 1
            echo 'Error: failed to compare portable Zed settings.' >&2
            return 1
        else if test $status_diff -eq 0
            echo "Unchanged $source_path"
        end
        return 0
    end

    __vscode_settings_write_targets "$tmp_path" "$source_path"
end

function __zed_settings_load_merge_engine
    if functions -q __vscode_settings_check_runtime \
            __vscode_settings_build_merged \
            __vscode_settings_load_ignored_keys \
            __vscode_settings_load_live_json \
            __vscode_settings_prepare_output \
            __vscode_settings_write_targets
        return 0
    end

    set -l function_path (functions --details zed-settings-apply)
    if test (count $function_path) -ne 1; or test -z "$function_path"
        echo 'Error: failed to locate the Zed settings function file.' >&2
        return 1
    end

    set -l engine_path (path dirname "$function_path")/vscode-settings-apply.fish
    if test -L "$engine_path"; or not test -f "$engine_path"
        printf 'Error: JSONC merge engine is not a regular file: %s\n' "$engine_path" >&2
        return 1
    end

    source "$engine_path"; or return 1
    if not functions -q __vscode_settings_check_runtime \
            __vscode_settings_build_merged \
            __vscode_settings_load_ignored_keys \
            __vscode_settings_load_live_json \
            __vscode_settings_prepare_output \
            __vscode_settings_write_targets
        echo 'Error: JSONC merge engine did not provide the required functions.' >&2
        return 1
    end
end

function __zed_settings_check_platform
    contains -- "$fish_platform" darwin linux wsl; and return 0
    printf 'Error: Zed settings sync does not support fish_platform=%s\n' "$fish_platform" >&2
    return 1
end

function __zed_settings_require_regular_file --argument-names input_path description
    if test -L "$input_path"; or not test -f "$input_path"
        printf 'Error: %s is not a regular file: %s\n' "$description" "$input_path" >&2
        return 1
    end
end
