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

        for scope in $fish_config_scopes
            __chezmoi_forget_existing "$fish_config_dir/conf.d/$scope"; or return 1
            __chezmoi_forget_existing "$fish_config_dir/functions/$scope"; or return 1
        end

        __chezmoi_add_files_by_extension "$fish_config_dir/conf.d" fish; or return 1
        __chezmoi_add_files_by_extension "$fish_config_dir/functions" fish; or return 1

        for scope in $fish_config_scopes
            __chezmoi_add_files_by_extension "$fish_config_dir/conf.d/$scope" fish; or return 1
            __chezmoi_add_files_by_extension "$fish_config_dir/functions/$scope" fish; or return 1
        end
    end

    set -l ghostty_config_dir "$HOME/.config/ghostty"
    if test -d "$ghostty_config_dir"
        __chezmoi_forget_existing "$ghostty_config_dir"; or return 1
        __chezmoi_add_existing "$ghostty_config_dir/config.ghostty"; or return 1
        __chezmoi_add_files_by_extension "$ghostty_config_dir/include" ghostty; or return 1
    end

    __chezmoi_forget_existing "$HOME/.config/starship.toml"; or return 1
    __chezmoi_add_existing "$HOME/.config/starship.toml"; or return 1
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
    test -d "$dir"; or return 0
    test -n "$extension"; or return 1

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
