#!/usr/bin/env fish

set -l __platform $fish_platform

__fish_load_config_dir "$__fish_config_dir/conf.d/$__platform"
__fish_load_config_dir "$__fish_config_dir/functions/$__platform"

if contains "$__platform" linux darwin wsl
    __fish_load_config_dir "$__fish_config_dir/conf.d/unix"
    __fish_load_config_dir "$__fish_config_dir/functions/unix"
end
