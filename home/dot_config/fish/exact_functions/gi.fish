#!/usr/bin/env fish

function gi --description "Initialize a new git repo with initial commit and rename branch"
    if not type -q git
        echo "❌ Git command not found."
        return 1
    end

    if test -d .git
        echo "⚠️ Git repository already exists."
        echo "❓ Do you want to delete .git directory and recreate it? [y/N]"
        read -l -P "" reply
        switch $reply
            case y Y
                echo "🗑️  Removing existing .git directory..."
                rm -rf .git; or return $status
            case '*'
                return 1
        end
    end

    echo "✨ Initializing new Git repository..."
    git init; or return $status

    echo "➕ Staging all files..."
    git add .; or return $status

    echo "📝 Creating initial commit..."
    git commit -m "Initial commit"; or return $status

    set -l branch (git rev-parse --abbrev-ref HEAD); or return $status
    if test "$branch" = master
        echo "🔀 Renaming branch 'master' to 'main'..."
        git branch -M main; or return $status
    end
    return 0
end
