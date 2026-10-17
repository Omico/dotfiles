#!/usr/bin/env fish

function chezmoi_add_configs --description 'Add local configuration files to chezmoi'
    set -l fish_config_dir "$HOME/.config/fish"
    set -l fish_config_scopes

    if contains "$fish_platform" linux darwin wsl
        set -a fish_config_scopes unix
    end
    set -a fish_config_scopes "$fish_platform"

    if test -d "$fish_config_dir"
        set -l fish_files "$fish_config_dir"/**/*.fish
        if test (count $fish_files) -gt 0
            fish_indent -w $fish_files; or return 1
        end

        find "$fish_config_dir" -type d -exec chmod 755 {} +; or return 1
        find "$fish_config_dir" -type f -exec chmod 644 {} +; or return 1

        __chezmoi_add_files_by_extension "$fish_config_dir/conf.d" fish; or return 1
        __chezmoi_add_files_by_extension "$fish_config_dir/functions" fish; or return 1

        for scope in $fish_config_scopes
            __chezmoi_add_files_by_extension "$fish_config_dir/conf.d/$scope" fish; or return 1
            __chezmoi_add_files_by_extension "$fish_config_dir/functions/$scope" fish; or return 1
        end
    end

    set -l ghostty_config_dir "$HOME/.config/ghostty"
    if test -d "$ghostty_config_dir"
        __chezmoi_add_files_by_extension "$ghostty_config_dir" ghostty; or return 1
        __chezmoi_add_files_by_extension "$ghostty_config_dir/include" ghostty; or return 1
    end

    __chezmoi_forget_existing "$HOME/.config/starship.toml"; or return 1
    __chezmoi_add_existing "$HOME/.config/starship.toml"; or return 1

    if type -q zed-settings-pull
        zed-settings-pull; or return $status
    end
end

function __chezmoi_forget_existing --argument-names target
    test -e "$target"; or return 0
    chezmoi forget --force "$target"
end

function __chezmoi_add_existing --argument-names target
    test -e "$target"; or return 0
    chezmoi add "$target"
end

function __chezmoi_add_files_by_extension --argument-names dir extension
    test -n "$extension"; or return 1

    set -l managed_files (chezmoi managed --include=files --path-style=absolute --nul-path-separator "$dir" | string split0)
    set -l managed_status $pipestatus[1]
    test $managed_status -eq 0; or return $managed_status

    for file in $managed_files
        test (path dirname "$file") = "$dir"; or continue
        string match -q "*.$extension" -- "$file"; or continue
        test -e "$file"; and continue
        test -L "$file"; and continue

        set -l source_path (chezmoi source-path "$file"); or return 1
        string match -q '*.tmpl' -- "$source_path"; and continue

        set -l previous_state (chezmoi state get --bucket entryState --key "$file" | string collect --allow-empty)
        set -l state_status $pipestatus[1]
        test $state_status -eq 0; or return $state_status
        if test -z "$previous_state"
            printf 'Keeping source file not yet applied: %s\n' "$source_path"
            continue
        end

        command -q jq; or begin
            echo 'Error: jq is required to check the last-applied file state.' >&2
            return 1
        end
        set -l previous_hash (printf '%s' "$previous_state" | command jq -er '.contentsSHA256 | select(type == "string" and test("^[a-f0-9]{64}$"))')
        or begin
            printf 'Error: invalid last-applied file state: %s\n' "$file" >&2
            return 1
        end

        set -l current_hash (chezmoi cat "$file" | chezmoi execute-template --with-stdin '{{ .chezmoi.stdin | sha256sum }}')
        set -l hash_status $pipestatus
        test $hash_status[1] -eq 0; and test $hash_status[2] -eq 0; or return 1
        if test "$current_hash" != "$previous_hash"
            printf 'Keeping source changes not yet applied: %s\n' "$source_path"
            continue
        end

        chezmoi forget --force "$file"; or return 1
    end

    test -d "$dir"; or return 0

    set -l files
    for file in "$dir"/*.$extension
        set -l source_path (chezmoi source-path "$file" 2>/dev/null)
        if test -n "$source_path"; and string match -q '*.tmpl' "$source_path"
            continue
        end
        set -a files "$file"
    end
    test (count $files) -gt 0; or return 0

    chezmoi add $files
end
