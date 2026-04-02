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

function __ensure_binary_and_forward --description 'internal: run installer if binary missing, then forward argv'
    set -l bin $argv[1]
    set -l name $argv[2]
    set -l shell $argv[3]
    set -l install $argv[4]

    if not test -x "$bin"
        printf "%s not found; installing...\n" $name >&2
        command $shell -c $install
        or begin
            printf "%s installation failed.\n" $name >&2
            return 1
        end
    end

    command $bin $argv[5..-1]
end
