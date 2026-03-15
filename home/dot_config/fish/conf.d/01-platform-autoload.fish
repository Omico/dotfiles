#!/usr/bin/env fish

__fish_load_config_dir "$__fish_config_dir/conf.d/$fish_platform"
__fish_load_config_dir "$__fish_config_dir/functions/$fish_platform"

if contains "$fish_platform" linux darwin wsl
    __fish_load_config_dir "$__fish_config_dir/conf.d/unix"
    __fish_load_config_dir "$__fish_config_dir/functions/unix"
end
