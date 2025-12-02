#!/usr/bin/env fish

function chezmoi_add_configs
    find ~/.config/fish -type d -exec chmod 755 {} \;
    find ~/.config/fish -type f -exec chmod 644 {} \;
    chezmoi forget --force ~/.config/fish/conf.d/
    chezmoi forget --force ~/.config/fish/functions/
    chezmoi forget --force ~/.config/starship.toml
    chezmoi add ~/.config/fish/conf.d/**/*.fish
    chezmoi add ~/.config/fish/functions/**/*.fish
    chezmoi add ~/.config/starship.toml
end
