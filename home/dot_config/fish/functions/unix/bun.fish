#!/usr/bin/env fish

function bun --description 'Ensure bun is installed, then run bun with given arguments'
    set -l bin "$HOME/.bun/bin/bun"
    if not test -x "$bin"
        printf "bun not found; installing via bun.sh...\n" >&2
        curl -fsSL https://bun.sh/install | bash
        or begin
            printf "bun installation failed.\n" >&2
            return 1
        end
    end
    command "$bin" $argv
end
