#!/usr/bin/env fish

function brew-backup --description "Backup Homebrew bundle to Brewfile"
  echo "Backing up Brewfile..."
  set -l BREWFILE_PATH "$HOME/.local/share/chezmoi/Brewfile"
  brew bundle dump --taps --brews --casks --mas --whalebrew --force --file="$BREWFILE_PATH"
  chezmoi git -- diff --quiet "$BREWFILE_PATH"; or begin
    chezmoi git -- add "$BREWFILE_PATH"
    chezmoi git -- commit -m "Update Brewfile"
  end
end

function brew-restore --description "Restore Homebrew packages from Brewfile"
  echo "Restoring Brewfile..."
  brew bundle --file="$HOME/.local/share/chezmoi/Brewfile"
end

function brew-update --description "Update Homebrew packages"
  brew update
  brew upgrade
  brew cleanup
  if type -q mas
      mas upgrade
  end
end

function brew-bump-omico --description "Bump omico/tap packages"
  brew bump --tap omico/tap --no-fork --open-pr
end
