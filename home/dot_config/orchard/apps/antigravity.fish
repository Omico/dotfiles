set -g orchard_app_id antigravity
set -g orchard_app_display_name Antigravity
set -g orchard_app_download_type zip

function orchard_resolve_download_url_callback
    set -l arch darwin
    if test (uname -m) = arm64
        set arch darwin-arm64
    end
    set -l json (curl -sL "https://antigravity-auto-updater-974169037036.us-central1.run.app/api/update/$arch/stable/latest" 2>/dev/null)
    if test -z "$json"
        echo "Failed to fetch Antigravity update API." >&2
        return 1
    end
    set -l url (echo "$json" | jq -r '.url')
    if test -z "$url"; or test "$url" = null
        echo "Could not parse download URL from API." >&2
        return 1
    end
    set -g orchard_app_download_url "$url"
    return 0
end

function orchard_after_install_callback
    _orchard_cli_symlink antigravity Contents/MacOS/Electron
end
