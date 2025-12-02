#!/usr/bin/env fish

function fish-reload --description "Reload the fish configuration"
    echo "🔄 Reloading fish configuration..."

    # Reload main config file
    if test -f "$__fish_config_dir/config.fish"
        source "$__fish_config_dir/config.fish"
        echo "✅ Reloaded "(string replace "$HOME" "~" "$__fish_config_dir/config.fish")
    end

    # Reload conf.d directory files (sorted alphabetically)
    for __config_file in $__fish_config_dir/conf.d/*.fish
        source "$__config_file"
        echo "✅ Reloaded "(string replace "$HOME" "~" "$__config_file")
    end

    echo "✨ Configuration reloaded!"
end
