#!/usr/bin/env fish

function update-jenv --description "Detect JDKs and add to jenv"
    set -l c_cyan (set_color cyan)
    set -l c_yellow (set_color yellow)
    set -l c_green (set_color -o green)
    set -l c_red (set_color -o red)
    set -l c_reset (set_color normal)

    if not test -d "$HOME/.jenv"
        echo $c_red"  ✗ jEnv not installed."$c_reset
        exit 1
    end

    rm -rf $HOME/.jenv/versions/*
    set -l found
    for jdk in /Library/Java/JavaVirtualMachines/*.jdk
        test -d "$jdk/Contents/Home" || continue
        echo $c_cyan"  → "$jdk$c_reset
        jenv add "$jdk/Contents/Home" >/dev/null 2>&1
        set found 1
    end

    if set -q found
        jenv rehash >/dev/null 2>&1
        echo $c_green"  ✓ Update complete, environment rehashed."$c_reset
    else
        echo $c_yellow"  ⚡ No JDKs found in /Library/Java/JavaVirtualMachines."$c_reset
    end
end
