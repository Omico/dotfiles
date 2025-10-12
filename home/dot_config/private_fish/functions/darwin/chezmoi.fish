#!/usr/bin/env fish

function chezmoi_add_configs
    chezmoi forget --force ~/.config/fish/conf.d/
    chezmoi forget --force ~/.config/fish/functions/
    chezmoi forget --force ~/.config/starship.toml
    chezmoi add ~/.config/fish/conf.d/**/*.fish
    chezmoi add ~/.config/fish/functions/**/*.fish
    chezmoi add ~/.config/starship.toml
end
