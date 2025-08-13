function dotfiles-upgrade() {
  echo "✨ Updating dotfiles with chezmoi..."
  chezmoi update
  chezmoi apply
  source "$HOME"/.zshrc

  echo "🔄 Updating Zinit..."
  zinit update --all --parallel 60

  echo "🍺 Updating Homebrew packages..."
  brewup update

  echo "🔤 Updating Rime configurations..."
  update-git-repo "$HOME/Library/Rime"
  cp -fv "$HOME"/.local/share/chezmoi/rime/*.custom.yaml "$HOME/Library/Rime/"

  echo "✅ All upgrades completed!"
}
