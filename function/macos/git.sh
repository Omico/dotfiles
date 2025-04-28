function gi() {
  if [ -d .git ]; then
    echo "⚠️ Git repository already exists."
    echo "❓ Do you want to delete it? [y/N]"
    read -k 1 REPLY
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

function update-git-repo() {
  local repo_dir="$1"

  if [ ! -d "$repo_dir/.git" ]; then
    echo "❌ Not a git repository: $repo_dir"
    return 1
  fi

  echo "🔄 Updating git repository: $repo_dir"
  git -C "$repo_dir" fetch --all || {
    echo "❌ Failed to fetch in $repo_dir"
    return 1
  }
  git -C "$repo_dir" reset --hard origin/HEAD || {
    echo "❌ Failed to reset in $repo_dir"
    return 1
  }
}
