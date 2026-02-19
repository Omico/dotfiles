#!/usr/bin/env fish

function dotfiles-upgrade --description "Upgrade dotfiles"
    echo "✨ Updating dotfiles with chezmoi..."
    chezmoi update
    chezmoi apply

    source $HOME/.config/fish/functions/fish-reload.fish
    fish-reload

    if test "$fish_platform" = darwin
        echo "🍺 Updating Homebrew packages..."
        brew-update

        if test -d "$HOME/Library/Rime"
            echo "🔤 Updating Rime configurations..."
            update-git-repo "$HOME/Library/Rime"; or echo "❌ Failed to update $HOME/Library/Rime"
            cp -fv "$HOME"/.local/share/chezmoi/rime/*.custom.yaml "$HOME/Library/Rime/"
        end
    end

    if contains "$fish_linux_distro" ubuntu
        echo "🐧 Updating Snap packages..."
        sudo snap refresh
    end

    command -q fnm; and fnm-upgrade-latest-lts

    echo "✅ All upgrades completed!"
end
