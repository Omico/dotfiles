#!/usr/bin/env fish

function update-git-repo --description "Fetch and hard reset a git repo to origin/HEAD"
    set -l repo_dir $argv[1]
    if test -z "$repo_dir"
        echo "❌ Missing repo directory argument"
        return 1
    end

    if not test -d "$repo_dir/.git"
        echo "❌ Not a git repository: $repo_dir"
        return 1
    end

    echo "🔄 Updating git repository: $repo_dir"
    git -C "$repo_dir" fetch --all; or begin
        echo "❌ Failed to fetch in $repo_dir"
        return 1
    end
    git -C "$repo_dir" reset --hard origin/HEAD; or begin
        echo "❌ Failed to reset in $repo_dir"
        return 1
    end
end
