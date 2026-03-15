#!/usr/bin/env fish

function chezmoi_add_configs
    set -l __fish_config_dir $HOME/.config/fish

    fish_indent -w $__fish_config_dir/**/*.fish

    find $__fish_config_dir -type d -exec chmod 755 {} \;
    find $__fish_config_dir -type f -exec chmod 644 {} \;

    chezmoi forget --force $__fish_config_dir/conf.d/$fish_platform
    chezmoi forget --force $__fish_config_dir/functions/$fish_platform

    chezmoi add $__fish_config_dir/conf.d/*.fish
    chezmoi add $__fish_config_dir/functions/*.fish

    if contains "$fish_platform" linux darwin wsl
        chezmoi add $__fish_config_dir/conf.d/$fish_platform/*.fish
        chezmoi add $__fish_config_dir/functions/$fish_platform/*.fish
    end

    chezmoi forget --force $HOME/.config/starship.toml
    chezmoi add $HOME/.config/starship.toml
end
