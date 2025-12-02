#!/usr/bin/env fish

function dotfiles-upgrade --description "Update dotfiles, Homebrew, and Rime"
  echo "✨ Updating dotfiles with chezmoi..."
  chezmoi update
  chezmoi apply

  echo "🍺 Updating Homebrew packages..."
  brew-update

  echo "🔤 Updating Rime configurations..."
  update-git-repo "$HOME/Library/Rime"; or echo "❌ Failed to update $HOME/Library/Rime"
  cp -fv "$HOME"/.local/share/chezmoi/rime/*.custom.yaml "$HOME/Library/Rime/"

  echo "🐟 Coping fish functions..."
  for file in "$HOME"/.local/share/chezmoi/functions/macos/*.fish
    cp -fv "$file" "$HOME/.config/fish/functions/"
  end

  echo "✅ All upgrades completed!"
end
