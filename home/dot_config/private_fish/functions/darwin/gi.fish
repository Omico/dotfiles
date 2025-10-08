#!/usr/bin/env fish

function gi --description "Initialize a new git repo with initial commit and rename branch"
  if test -d .git
    echo "⚠️ Git repository already exists."
    echo "❓ Do you want to delete .git directory and recreate it? [y/N]"
    read -l -P "" reply
    switch $reply
      case y Y
        echo "🗑️  Removing existing .git directory..."
        rm -rf .git
      case '*'
        return 1
    end
  end

  echo "✨ Initializing new Git repository..."
  git init

  echo "➕ Staging all files..."
  git add .

  echo "📝 Creating initial commit..."
  git commit -m "Initial commit"

  if git rev-parse --abbrev-ref HEAD 2>/dev/null | grep -q '^master$'
    echo "🔀 Renaming branch 'master' to 'main'..."
    git branch -M main
  end
end
