#!/usr/bin/env fish

function fnm-upgrade-latest-lts --description "Install LTS, set default, uninstall other Node versions"
    command -q fnm; or begin
        echo "fnm: command not found" >&2
        return 1
    end

    set -l latest_lts (fnm list-remote --lts --latest 2>/dev/null | awk '{print $1}')
    set -l installed (fnm list 2>/dev/null | awk '{print $2}' | string match -r '^v')

    if test -z "$latest_lts"; or not contains "$latest_lts" $installed
        fnm install --lts; or return 1
        set latest_lts (fnm list-remote --lts --latest 2>/dev/null | awk '{print $1}')
    end

    if test -z "$latest_lts"
        echo "fnm: could not resolve latest LTS version" >&2
        return 1
    end

    fnm use "$latest_lts"; or return 1
    fnm default "$latest_lts"; or return 1

    for v in (fnm list 2>/dev/null | awk '{print $2}' | string match -r '^v')
        if test "$v" != "$latest_lts"
            fnm uninstall $v; or printf "fnm: failed to uninstall %s\n" $v >&2
        end
    end

    if not command -q pnpm
        command -q corepack; or npm install -g corepack@latest
        command -q corepack; and begin
            corepack enable
            corepack install -g pnpm@latest
        end
    end
end
