function brew-backup() {
  echo "Backing up Brewfile..."
  local BREWFILE_PATH="$HOME/.local/share/chezmoi/Brewfile"
  brew bundle dump --taps --brews --casks --mas --whalebrew --force --file="$BREWFILE_PATH"
  chezmoi git -- diff --quiet "$BREWFILE_PATH" || {
    chezmoi git -- add "$BREWFILE_PATH"
    chezmoi git -- commit -m "Update Brewfile"
  }
}

function brew-restore() {
  echo "Restoring Brewfile..."
  brew bundle --file="$HOME/.local/share/chezmoi/Brewfile"
}

function brew-update() {
  brew update
  brew upgrade
  brew cleanup
  mas upgrade
}
