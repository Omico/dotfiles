#!/usr/bin/env fish

set -l __platform $fish_platform

function __load_dir
    set -l dir $argv[1]
    test -z "$dir"; and return
    if test -d "$dir"
        for f in "$dir"/*.fish
            test -r "$f"; and source "$f"
        end
    end
end

__load_dir "$__fish_config_dir/conf.d/$__platform"
__load_dir "$__fish_config_dir/functions/$__platform"

if contains "$__platform" linux darwin wsl
    __load_dir "$__fish_config_dir/conf.d/unix"
    __load_dir "$__fish_config_dir/functions/unix"
end

functions -e __load_dir
