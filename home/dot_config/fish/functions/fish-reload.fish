#!/usr/bin/env fish

function fish-reload --description "Reload the fish configuration"
    set -l _verbose 0

    if test (count $argv) -gt 0
        switch $argv[1]
            case -v --verbose
                set _verbose 1
            case '*'
                echo "Usage: fish-reload [-v|--verbose]" >&2
                return 1
        end
    end

    if test $_verbose -eq 1
        echo "🔄 Reloading fish configuration..."
    end

    # Reload main config file
    if test -f "$__fish_config_dir/config.fish"
        source "$__fish_config_dir/config.fish"
        if test $_verbose -eq 1
            echo "✅ Reloaded "(string replace "$HOME" "~" "$__fish_config_dir/config.fish")
        end
    end

    # Reload conf.d directory files (sorted alphabetically)
    for __config_file in $__fish_config_dir/conf.d/*.fish
        source "$__config_file"
        if test $_verbose -eq 1
            echo "✅ Reloaded "(string replace "$HOME" "~" "$__config_file")
        end
    end

    echo "✨ Configuration reloaded!"
end
