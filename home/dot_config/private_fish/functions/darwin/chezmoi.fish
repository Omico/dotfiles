#!/usr/bin/env fish

function chezmoi_add_configs
    chezmoi add ~/.config/fish/conf.d/**/*.fish
    chezmoi add ~/.config/fish/functions/**/*.fish
    chezmoi add ~/.config/starship.toml
end
