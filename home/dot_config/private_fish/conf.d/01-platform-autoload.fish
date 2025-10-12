#!/usr/bin/env fish

set -l __platform $fish_platform

set -l __conf_dir "$__fish_config_dir/conf.d/$__platform"
if test -d "$__conf_dir"
    for f in "$__conf_dir"/*.fish
        test -r "$f"; and source "$f"
    end
end

set -l __func_dir "$__fish_config_dir/functions/$__platform"
if test -d "$__func_dir"
    for f in "$__func_dir"/*.fish
        test -r "$f"; and source "$f"
    end
end
