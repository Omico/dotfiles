#!/usr/bin/env fish

if not set -q fish_platform
    set -l u (uname)
    switch $u
        case Darwin
            set -g fish_platform "darwin"
        case Linux
            if string match -q "*microsoft*" (uname -r)
                set -g fish_platform "wsl"
            else
                set -g fish_platform "linux"
            end
        case CYGWIN_NT* MSYS_NT* MINGW*
            set -g fish_platform "msys"
        case '*'
            set -g fish_platform "other"
    end
end
