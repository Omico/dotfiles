#!/usr/bin/env fish

function fnm-upgrade-latest-lts --description "Install LTS, set default, uninstall other Node versions"
    command -q fnm; or begin
        echo "fnm: command not found"
        return 1
    end
    set -l latest_lts (fnm list-remote --lts 2>/dev/null | tail -1 | awk '{print $1}')
    set -l installed (fnm list 2>/dev/null | awk '{print $2}' | grep -E '^v')
    if test -z "$latest_lts" || not contains "$latest_lts" $installed
        fnm install --lts; or return 1
    end
    fnm use "$latest_lts"; or return 1
    fnm default "$latest_lts"
    for v in (fnm list | awk '{print $2}' | grep -E '^v' | grep -v "^$latest_lts\$")
        fnm uninstall $v
    end
end
