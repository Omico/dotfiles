#!/usr/bin/env fish

function brew-backup --description "Backup Homebrew bundle to Brewfile"
    set -l brewfile "$HOME/.local/share/chezmoi/Brewfile"
    echo "Backing up Brewfile..."
    brew bundle dump --taps --brews --casks --mas --force --file="$brewfile"
    chezmoi git -- diff --quiet "$brewfile"; or begin
        chezmoi git -- add "$brewfile"
        chezmoi git -- commit -m "Update Brewfile"
    end
end

function brew-restore --description "Restore Homebrew packages from Brewfile"
    set -l brewfile "$HOME/.local/share/chezmoi/Brewfile"
    echo "Restoring Brewfile..."
    brew bundle --file="$brewfile"
end

function brew-update --description "Update Homebrew packages"
    brew update
    brew upgrade
    brew cleanup
    brew autoremove
    if type -q mas
        mas upgrade
    end
end

function brew-bump-omico --description "Bump omico/tap packages"
    brew bump --tap omico/tap --no-fork --open-pr
end
