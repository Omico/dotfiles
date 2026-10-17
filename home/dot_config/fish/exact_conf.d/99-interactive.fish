#!/usr/bin/env fish

if status --is-interactive
    # Aliases
    alias fish_edit_config='$EDITOR ~/.config/fish/config.fish'

    # jEnv
    if command -q jenv
        function jenv
            functions -e jenv
            source (command jenv init - | psub)
            jenv $argv
        end
    end

    # rbenv
    if command -q rbenv
        function rbenv
            functions -e rbenv
            source (command rbenv init - | psub)
            rbenv $argv
        end
    end

    # thefuck
    if command -q thefuck
        function fuck
            functions -e fuck
            thefuck --alias fuck | source
            fuck $argv
        end
    end
end
