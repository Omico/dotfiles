#!/usr/bin/env fish

function vscode-settings-apply --description 'Merge vscode-settings into Code/Cursor User settings'
    __vscode_settings_check_runtime; or return 1

    set -l source_dir "$HOME/.config/vscode-settings"
    set -l shared_path "$source_dir/shared.json"
    if test -L "$shared_path"; or not test -f "$shared_path"
        echo "Error: shared settings is not a regular file: $shared_path" >&2
        return 1
    end

    set -l prepared_targets
    set -l temp_paths
    for app in code cursor
        set -l live_path (__vscode_settings_live_path $app)
        or begin
            command rm -f $temp_paths
            return 1
        end

        set -l tmp_path (__vscode_settings_prepare_output "$live_path")
        or begin
            command rm -f $temp_paths
            return 1
        end
        set -a temp_paths "$tmp_path"

        __vscode_settings_build_merged \
            "$shared_path" \
            "$source_dir/$app.json" \
            "$source_dir/ignored.json" \
            "$source_dir/$app.ignored.json" \
            "$live_path" \
            "$tmp_path"
        or begin
            printf "Error: failed to merge %s settings.\n" $app >&2
            command rm -f $temp_paths
            return 1
        end

        set -a prepared_targets "$tmp_path" "$live_path"
    end

    __vscode_settings_write_targets $prepared_targets
end

# Runtime and platform helpers

function __vscode_settings_check_runtime
    if not set -q fish_platform
        echo "Error: fish_platform is not set. Run chezmoi apply, then open a new Fish shell." >&2
        return 1
    end

    command -q jq; or begin
        echo "Error: jq is required to merge vscode-settings." >&2
        return 1
    end
    command -q iconv; or begin
        echo "Error: iconv is required to validate vscode-settings input." >&2
        return 1
    end

    set -l jq_number_probe (
        printf '{"value":9007199254740993}\n' \
            | command jq --compact-output --slurp '
                if length != 1 then
                    error("expected exactly one JSON document")
                elif any(.[0] | .. | numbers; isnan or isinfinite) then
                    error("JSON number is out of range")
                else
                    .[0] + {}
                end
            '
    )
    set -l status_jq_probe $pipestatus[2]
    if test $status_jq_probe -ne 0; or test "$jq_number_probe" != '{"value":9007199254740993}'
        echo "Error: jq 1.7 or newer with literal-number preservation is required." >&2
        return 1
    end
end

function __vscode_settings_live_path --argument-names app
    switch $fish_platform
        case darwin
            switch $app
                case code
                    echo "$HOME/Library/Application Support/Code/User/settings.json"
                case cursor
                    echo "$HOME/Library/Application Support/Cursor/User/settings.json"
                case '*'
                    printf "Error: unknown vscode-settings app: %s\n" $app >&2
                    return 1
            end
        case linux wsl
            switch $app
                case code
                    echo "$HOME/.config/Code/User/settings.json"
                case cursor
                    echo "$HOME/.config/Cursor/User/settings.json"
                case '*'
                    printf "Error: unknown vscode-settings app: %s\n" $app >&2
                    return 1
            end
        case '*'
            printf "Error: vscode-settings-apply does not support fish_platform=%s\n" $fish_platform >&2
            return 1
    end
end

# Input parsing helpers

function __vscode_settings_read_object --argument-names input_path display_path description
    if test -L "$input_path"; or not test -f "$input_path"
        printf "Error: %s is not a regular file: %s\n" "$description" "$display_path" >&2
        return 1
    end

    __vscode_settings_validate_utf8 "$input_path" "$display_path" "$description"; or return 1

    set -l source (command cat -- "$input_path" | string collect --no-trim-newlines --allow-empty)
    set -l status_read $pipestatus[1]
    if test $status_read -ne 0
        printf "Error: failed to read %s: %s\n" "$description" "$display_path" >&2
        return 1
    end

    __vscode_settings_validate_json_lexemes "$source" "$display_path"; or return 1

    printf '%s' "$source" | command jq --indent 2 --slurp '
        if length != 1 then
            error("expected exactly one JSON document")
        elif (.[0] | type) != "object" then
            error("expected a JSON object")
        elif any(.[0] | .. | numbers; isnan or isinfinite) then
            error("JSON number is out of range")
        else
            .[0]
        end
    '
    set -l status_jq $pipestatus[2]
    if test $status_jq -ne 0
        printf "Error: invalid %s: %s\n" "$description" "$display_path" >&2
    end
    return $status_jq
end

function __vscode_settings_validate_json_lexemes --argument-names source display_path
    set -l without_strings (
        string replace -ra '"(?:\\\\[\s\S]|[^"\\\\])*"' ' ' -- "$source" \
            | string collect --no-trim-newlines --allow-empty
    )
    set -l status_strings $pipestatus[1]
    if test $status_strings -gt 1
        return $status_strings
    end

    if string match -rq \
            '(?i:(?<![A-Za-z0-9_])-?(?:nan|infinity|inf)(?![A-Za-z0-9_]))' \
            -- "$without_strings"
        printf "Error: non-standard JSON constant: %s\n" "$display_path" >&2
        return 1
    end

    for number in (string match -ra \
            '[-+]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][-+]?[0-9]*)?' \
            -- "$without_strings")
        if not string match -qr \
                '^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?$' \
                -- "$number"
            printf "Error: non-standard JSON number in %s: %s\n" "$display_path" "$number" >&2
            return 1
        end
    end
    return 0
end

function __vscode_settings_load_ignored_keys --argument-names shared_ignored_path app_ignored_path
    set -l shared_tmp (mktemp)
    set -l app_tmp (mktemp)

    __vscode_settings_read_ignored_file "$shared_ignored_path" >"$shared_tmp"
    or begin
        command rm -f "$shared_tmp" "$app_tmp"
        return 1
    end

    __vscode_settings_read_ignored_file "$app_ignored_path" >"$app_tmp"
    or begin
        command rm -f "$shared_tmp" "$app_tmp"
        return 1
    end

    command jq --indent 2 --slurp 'add | unique' "$shared_tmp" "$app_tmp"
    set -l status_jq $status
    command rm -f "$shared_tmp" "$app_tmp"
    return $status_jq
end

function __vscode_settings_read_ignored_file --argument-names ignored_path
    if test -L "$ignored_path"
        printf "Error: ignored input is not a regular file: %s\n" "$ignored_path" >&2
        return 1
    else if not test -f "$ignored_path"
        if test -e "$ignored_path"
            printf "Error: ignored input is not a regular file: %s\n" "$ignored_path" >&2
            return 1
        else
            echo '[]'
            return 0
        end
    end

    __vscode_settings_validate_utf8 "$ignored_path" "$ignored_path" "ignored file"; or return 1

    set -l source (command cat -- "$ignored_path" | string collect --no-trim-newlines --allow-empty)
    set -l status_read $pipestatus[1]
    if test $status_read -ne 0
        printf "Error: failed to read ignored file: %s\n" "$ignored_path" >&2
        return 1
    end

    __vscode_settings_validate_json_lexemes "$source" "$ignored_path"; or return 1

    printf '%s' "$source" | command jq --indent 2 --slurp '
        if length != 1 then
            error("expected exactly one JSON document")
        elif (.[0] | type) != "array" then
            error("expected an array")
        elif (all(.[0][]; type == "string") | not) then
            error("expected only strings")
        else
            .[0]
        end
    '
    set -l status_jq $pipestatus[2]
    if test $status_jq -ne 0
        printf "Error: ignored file must be a JSON array of strings: %s\n" "$ignored_path" >&2
    end
    return $status_jq
end

function __vscode_settings_load_live_json --argument-names live_path
    if not test -f "$live_path"
        echo '{}'
        return 0
    end

    __vscode_settings_validate_utf8 "$live_path" "$live_path" "live settings"; or return 1

    set -l source (command cat -- "$live_path" | string collect --no-trim-newlines --allow-empty)
    set -l status_read $pipestatus[1]
    if test $status_read -ne 0
        printf "Error: failed to read live settings: %s\n" "$live_path" >&2
        return 1
    end

    set -l cleaned (mktemp); or return 1
    set -l parsed (mktemp); or begin
        command rm -f "$cleaned"
        return 1
    end

    __vscode_settings_normalize_jsonc "$source" "$live_path" >"$cleaned"
    or begin
        command rm -f "$cleaned" "$parsed"
        return 1
    end

    __vscode_settings_read_object "$cleaned" "$live_path" "live settings" >"$parsed"
    or begin
        command rm -f "$cleaned" "$parsed"
        return 1
    end

    command cat -- "$parsed"
    set -l status_cat $status
    command rm -f "$cleaned" "$parsed"
    return $status_cat
end

function __vscode_settings_validate_utf8 --argument-names input_path display_path description
    command iconv -f UTF-8 -t UTF-8 "$input_path" >/dev/null 2>&1
    set -l status_iconv $status
    if test $status_iconv -ne 0
        printf "Error: invalid UTF-8 in %s: %s\n" "$description" "$display_path" >&2
        return $status_iconv
    end

    begin
        set -lx LC_ALL C
        command tr -d '\000' <"$input_path"
    end | command cmp -s - "$input_path"
    set -l status_nul_check $pipestatus
    if test $status_nul_check[1] -ne 0; or test $status_nul_check[2] -gt 1
        printf "Error: failed to validate raw bytes in %s: %s\n" \
            "$description" "$display_path" >&2
        return 1
    else if test $status_nul_check[2] -eq 1
        printf "Error: raw NUL byte in %s: %s\n" "$description" "$display_path" >&2
        return 1
    end
    return 0
end

function __vscode_settings_normalize_jsonc --argument-names source source_path
    set -l without_bom (
        string replace -r '^\x{FEFF}' '' -- "$source" \
            | string collect --no-trim-newlines --allow-empty
    )
    set -l status_bom $pipestatus[1]
    if test $status_bom -gt 1
        return $status_bom
    end

    set -l without_comments (
        string replace -ra \
            '"(?:\\\\[\s\S]|[^"\\\\])*"(*SKIP)(*F)|//[^\r\n]*|/\*(?:[^*]|\*(?!/))*\*/' \
            ' ' \
            -- "$without_bom" \
            | string collect --no-trim-newlines --allow-empty
    )
    set -l status_comments $pipestatus[1]
    if test $status_comments -gt 1
        return $status_comments
    end

    string match -rq \
        '"(?:\\\\[\s\S]|[^"\\\\])*"(*SKIP)(*F)|[{\[,]([ \t\r\n]*),[ \t\r\n]*(?=[}\]])' \
        -- "$without_comments"
    set -l status_empty_entry $status
    if test $status_empty_entry -eq 0
        printf "Error: invalid empty JSONC entry in live settings: %s\n" "$source_path" >&2
        return 1
    else if test $status_empty_entry -gt 1
        return $status_empty_entry
    end

    string replace -ra \
        '"(?:\\\\[\s\S]|[^"\\\\])*"(*SKIP)(*F)|,(?=[ \t\r\n]*[}\]])' \
        ' ' \
        -- "$without_comments"
    set -l status_commas $status
    if test $status_commas -gt 1
        return $status_commas
    end
    return 0
end

# Merge preparation

function __vscode_settings_build_merged \
    --argument-names shared_path unique_path shared_ignored_path app_ignored_path live_path output_path
    set -l work_dir (mktemp -d); or return 1

    set -l managed_path "$work_dir/managed.json"
    set -l ignored_path "$work_dir/ignored.json"
    set -l managed_prime_path "$work_dir/managed_prime.json"
    set -l live_clean_path "$work_dir/live.json"

    set -l managed_inputs "$shared_path"
    if test -f "$unique_path"
        set -a managed_inputs "$unique_path"
    else if test -e "$unique_path"; or test -L "$unique_path"
        printf "Error: settings layer is not a regular file: %s\n" "$unique_path" >&2
        command rm -rf "$work_dir"
        return 1
    end

    set -l managed_clean_inputs
    set -l managed_index 0
    for settings_path in $managed_inputs
        set managed_index (math $managed_index + 1)
        set -l managed_clean_path "$work_dir/managed-$managed_index.json"
        __vscode_settings_read_object "$settings_path" "$settings_path" "settings layer" >"$managed_clean_path"
        or begin
            command rm -rf "$work_dir"
            return 1
        end
        set -a managed_clean_inputs "$managed_clean_path"
    end

    command jq --indent 2 --slurp 'reduce .[] as $item ({}; . + $item)' \
        $managed_clean_inputs >"$managed_path"
    or begin
        command rm -rf "$work_dir"
        return 1
    end

    __vscode_settings_load_ignored_keys "$shared_ignored_path" "$app_ignored_path" >"$ignored_path"
    or begin
        command rm -rf "$work_dir"
        return 1
    end

    command jq --indent 2 --slurp \
        '.[0] as $managed | .[1] as $ignored | reduce $ignored[] as $key ($managed; del(.[$key]))' \
        "$managed_path" "$ignored_path" >"$managed_prime_path"
    or begin
        command rm -rf "$work_dir"
        return 1
    end

    __vscode_settings_load_live_json "$live_path" >"$live_clean_path"
    or begin
        command rm -rf "$work_dir"
        return 1
    end

    command jq --indent 2 --slurp '.[0] + .[1]' \
        "$live_clean_path" "$managed_prime_path" >"$output_path"
    set -l status_merge $status
    command rm -rf "$work_dir"
    return $status_merge
end

# Transactional target writes

function __vscode_settings_prepare_output --argument-names live_path
    if test -L "$live_path"; or begin
            test -e "$live_path"
            and not test -f "$live_path"
        end
        printf "Error: live settings target is not a regular file: %s\n" "$live_path" >&2
        return 1
    end

    command mkdir -p (path dirname "$live_path"); or return 1

    set -l tmp_path (mktemp "$live_path.tmp.XXXXXX"); or return 1
    if test -f "$live_path"
        command cp -p "$live_path" "$tmp_path"; or begin
            command rm -f "$tmp_path"
            return 1
        end
    end

    echo "$tmp_path"
end

function __vscode_settings_write_targets
    if test (math (count $argv) % 2) -ne 0
        echo "Error: prepared vscode-settings targets must be temp/live pairs." >&2
        return 1
    end

    set -l temp_paths
    set -l live_paths
    for pair_start in (command seq 1 2 (count $argv))
        set -l live_position (math $pair_start + 1)
        set -a temp_paths $argv[$pair_start]
        set -a live_paths $argv[$live_position]
    end

    set -l changed_indices
    set -l backup_paths
    for index in (command seq (count $temp_paths))
        set -l tmp_path $temp_paths[$index]
        set -l live_path $live_paths[$index]
        if test -f "$live_path"
            command cmp -s "$tmp_path" "$live_path"
            set -l status_cmp $status
            if test $status_cmp -eq 0
                command rm -f "$tmp_path"
                echo "Unchanged $live_path"
                continue
            else if test $status_cmp -gt 1
                printf "Error: failed to compare generated and live settings: %s\n" \
                    "$live_path" >&2
                command rm -f $temp_paths $backup_paths
                return 1
            end
        end

        set -a changed_indices $index
        set -l backup_path ""
        if test -f "$live_path"
            set backup_path (mktemp "$live_path.backup.XXXXXX"); or begin
                command rm -f $temp_paths $backup_paths
                return 1
            end
            command cp -p "$live_path" "$backup_path"; or begin
                command rm -f "$backup_path" $temp_paths $backup_paths
                return 1
            end
        end
        set -a backup_paths "$backup_path"
    end

    set -l replaced_count 0
    if test (count $changed_indices) -gt 0
        for position in (command seq (count $changed_indices))
            set -l index $changed_indices[$position]
            set -l tmp_path $temp_paths[$index]
            set -l live_path $live_paths[$index]
            if command mv "$tmp_path" "$live_path"
                set replaced_count (math $replaced_count + 1)
                continue
            end

            printf "Error: failed to write %s\n" "$live_path" >&2
            set -l rollback_failed 0
            if test $replaced_count -gt 0
                for offset in (command seq $replaced_count)
                    set -l rollback_position (math $replaced_count - $offset + 1)
                    set -l rollback_index $changed_indices[$rollback_position]
                    set -l rollback_live_path $live_paths[$rollback_index]
                    set -l rollback_backup_path $backup_paths[$rollback_position]
                    if test -n "$rollback_backup_path"
                        command mv "$rollback_backup_path" "$rollback_live_path"; or begin
                            printf "Error: failed to restore %s from %s\n" \
                                "$rollback_live_path" "$rollback_backup_path" >&2
                            set rollback_failed 1
                        end
                    else
                        command rm -f "$rollback_live_path"; or begin
                            printf "Error: failed to remove newly created %s during rollback\n" \
                                "$rollback_live_path" >&2
                            set rollback_failed 1
                        end
                    end
                end
            end

            set -l first_unused_backup (math $replaced_count + 1)
            if test $first_unused_backup -le (count $backup_paths)
                for cleanup_position in (command seq $first_unused_backup (count $backup_paths))
                    set -l cleanup_backup_path $backup_paths[$cleanup_position]
                    test -n "$cleanup_backup_path"; and command rm -f "$cleanup_backup_path"
                end
            end
            command rm -f $temp_paths 2>/dev/null
            test $rollback_failed -eq 0; or echo "Error: rollback was incomplete." >&2
            return 1
        end
    end

    command rm -f $temp_paths $backup_paths 2>/dev/null
    for index in $changed_indices
        echo "Updated $live_paths[$index]"
    end
end
