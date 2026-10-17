#!/usr/bin/env fish

function gitkraken --description "Open GitKraken (optionally with a project path). Use GITKRAKEN_APP_PATH to customize installation path"
    if test (count $argv) -gt 1
        echo "gitkraken: error: too many arguments" >&2
        echo "Usage: gitkraken [project_path]" >&2
        return 1
    end

    set -l gitkraken_app
    if test -n "$GITKRAKEN_APP_PATH"
        set gitkraken_app "$GITKRAKEN_APP_PATH"
    else
        set gitkraken_app /Applications/GitKraken.app
    end

    set -l gitkraken_bin "$gitkraken_app/Contents/MacOS/GitKraken"
    if not test -d "$gitkraken_app"
        echo "gitkraken: error: GitKraken not found at $gitkraken_app" >&2
        echo "  Set GITKRAKEN_APP_PATH to customize the installation path" >&2
        return 1
    end
    if not test -x "$gitkraken_bin"
        echo "gitkraken: error: executable not found or not executable: $gitkraken_bin" >&2
        return 1
    end

    set -l project_path $argv[1]
    if test -z "$project_path"
        "$gitkraken_bin" >/dev/null 2>&1 &
        echo "✨ Opening GitKraken..."
        return
    end

    set -l absolute_path (realpath (eval echo "$project_path") 2>/dev/null)
    if test -z "$absolute_path" -o ! -d "$absolute_path"
        echo "gitkraken: error: directory not found: $project_path" >&2
        return 1
    end

    "$gitkraken_bin" -p "$absolute_path" >/dev/null 2>&1 &
    echo "✨ Opening GitKraken with project: $absolute_path"
end
