#!/usr/bin/env fish

function fnm-upgrade-latest-lts --description "Install LTS, set default, uninstall other Node versions"
    command -q fnm; or begin
        echo "fnm: command not found" >&2
        return 1
    end

    set -l installed (__fnm_installed_node_versions)
    set -l latest_lts

    for _attempt in 1 2
        set latest_lts (__fnm_remote_latest_lts)
        if test -n "$latest_lts"; and contains "$latest_lts" $installed
            break
        end
        test $_attempt -eq 1; or break
        fnm install --lts; or return $status
        set installed (__fnm_installed_node_versions)
    end

    if test -z "$latest_lts"
        echo "fnm: could not resolve latest LTS version" >&2
        return 1
    end

    fnm use "$latest_lts"; or return $status
    fnm default "$latest_lts"; or return $status

    for v in $installed
        if test "$v" != "$latest_lts"
            fnm uninstall "$v"; or return $status
        end
    end

    if not command -q pnpm
        if not command -q corepack
            npm install -g corepack@latest; or return $status
        end
        corepack enable; or return $status
        corepack install -g pnpm@latest; or return $status
    end
    return 0
end

function __fnm_installed_node_versions --description 'internal: installed Node semver list from fnm list'
    fnm list 2>/dev/null | awk '{print $2}' | string match -r '^v[0-9]+\.[0-9]+\.[0-9]+'
end

function __fnm_remote_latest_lts --description 'internal: latest LTS semver from fnm list-remote'
    string split -f1 ' ' -- (fnm list-remote --lts --latest 2>/dev/null)
end
