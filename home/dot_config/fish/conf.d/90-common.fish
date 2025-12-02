#!/usr/bin/env fish

set -g fish_greeting ""
set -U fish_color_command green

set -gx LC_ALL en_US.UTF-8

if test -d $HOME/bin
    fish_add_path $HOME/bin
end

if test -d $HOME/.local/bin
    fish_add_path $HOME/.local/bin
end
