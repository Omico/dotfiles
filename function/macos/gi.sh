function gi() {
  if [ -d .git ]; then
    echo "⚠️ Git repository already exists."
    read -rp "❓ Do you want to delete it? [y/N]" REPLY
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      echo "🗑️  Removing existing .git directory..."
      rm -rf .git
    else
      return 1
    fi
  fi

  echo "✨ Initializing new Git repository..."
  git init

  echo "➕ Staging all files..."
  git add .

  echo "📝 Creating initial commit..."
  git commit -m "Initial commit"

  if git rev-parse --abbrev-ref HEAD 2>/dev/null | grep -q '^master$'; then
    echo "🔀 Renaming branch 'master' to 'main'..."
    git branch -M main
  fi
}
