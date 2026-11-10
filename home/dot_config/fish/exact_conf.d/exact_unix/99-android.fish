#!/usr/bin/env fish

if command -q android
    set -l android_sdk (command android info sdk 2>/dev/null)
    if test $status -eq 0; and test -n "$android_sdk"; and test -d "$android_sdk/platform-tools"
        fish_add_path --path "$android_sdk/platform-tools"
    end
end
