#!/usr/bin/env fish

function chezmoi_add_configs
    set fish_config ~/.config/fish

    fish_indent -w $fish_config/**/*.fish

    find $fish_config -type d -exec chmod 755 {} \;
    find $fish_config -type f -exec chmod 644 {} \;

    chezmoi forget --force $fish_config/conf.d/
    chezmoi forget --force $fish_config/functions/

    chezmoi add $fish_config/conf.d/**/*.fish
    chezmoi add $fish_config/functions/**/*.fish

    chezmoi forget --force ~/.config/starship.toml
    chezmoi add ~/.config/starship.toml
end
