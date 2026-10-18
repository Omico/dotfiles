#!/usr/bin/env fish

function brew-backup --description "Backup Homebrew bundle to Brewfile"
    set -l brewfile "$HOME/.local/share/chezmoi/Brewfile"
    echo "Backing up Brewfile..."
    brew bundle dump --taps --brews --casks --mas --force --file="$brewfile"; or return $status
    chezmoi git -- diff --quiet "$brewfile"
    set -l diff_status $status
    switch $diff_status
        case 0
            return 0
        case 1
            chezmoi git -- add "$brewfile"; or return $status
            chezmoi git -- commit -m "Update Brewfile"
        case '*'
            return $diff_status
    end
end

function brew-restore --description "Restore Homebrew packages from Brewfile"
    set -l brewfile "$HOME/.local/share/chezmoi/Brewfile"
    echo "Restoring Brewfile..."
    brew bundle --file="$brewfile"
end

function brew-update --description "Update Homebrew packages"
    echo "🍺 Updating Homebrew packages..."
    brew update; or return $status
    brew upgrade; or return $status
    brew cleanup; or return $status
    brew autoremove; or return $status
    if type -q mas
        mas upgrade; or return $status
    end
    return 0
end

function brew-bump-omico --description "Bump omico/tap packages"
    brew bump --tap omico/tap --no-fork --open-pr
end
