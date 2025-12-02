#!/usr/bin/env fish

function fish_add_path_if_exists
    for dir in $argv
        if test -d "$dir"
            fish_add_path "$dir"
        end
    end
end

function fish_add_android_sdk_root
    set -l android_sdk_root $argv[1]
    test -z "$android_sdk_root"; and return
    if test -d "$android_sdk_root"
        set -gx ANDROID_SDK_ROOT "$android_sdk_root"
        # For legacy reasons, some tools expect ANDROID_HOME to be set
        set -gx ANDROID_HOME "$ANDROID_SDK_ROOT"
        fish_add_path_if_exists "$android_sdk_root/platform-tools"
    end
end

function __fish_load_config_dir
    set -l dir $argv[1]
    test -z "$dir"; and return
    if test -d "$dir"
        for f in "$dir"/*.fish
            test -r "$f"; and source "$f"
        end
    end
end
