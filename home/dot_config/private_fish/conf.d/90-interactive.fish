#!/usr/bin/env fish

if status --is-interactive
    # Aliases
    alias fish_edit_config='code ~/.config/fish/config.fish'
    alias fish_reload='source ~/.config/fish/config.fish'

    # Fast Node Manager (fnm)
    if type -q fnm
        fnm env --use-on-cd --shell fish | source
    end

    # GitHub CLI
    if type -q gh
        gh completion -s fish | source
    end

    # jEnv
    if test -d $HOME/.jenv
        fish_add_path $HOME/.jenv/bin
        source (jenv init - | psub)
    end

    # rbenv
    if type -q rbenv
        source (rbenv init - | psub)
    end

    # thefuck
    if type -q thefuck
        thefuck --alias | source
    end
end
