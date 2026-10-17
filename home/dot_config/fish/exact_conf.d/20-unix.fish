#!/usr/bin/env fish

if contains "$fish_platform" linux darwin wsl
    __fish_load_config_dir "$__fish_config_dir/functions/unix"
    __fish_load_config_dir "$__fish_config_dir/conf.d/unix"
end
