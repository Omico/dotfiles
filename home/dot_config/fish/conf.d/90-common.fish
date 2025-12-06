#!/usr/bin/env fish

set -g fish_greeting ""
set -U fish_color_command green

set -gx LC_ALL en_US.UTF-8

set -gx EDITOR code

fish_add_path_if_exists "$HOME/bin" "$HOME/.local/bin"
