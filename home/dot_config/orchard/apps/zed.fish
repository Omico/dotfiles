set -g orchard_app_id zed
set -g orchard_app_display_name Zed
set -g orchard_app_download_type dmg

function orchard_resolve_download_url_callback
    set -l arch x86_64
    if test (uname -m) = arm64
        set arch aarch64
    end

    set -l json (curl -fsSL "https://zed.dev/api/releases/latest?asset=Zed.dmg&stable=1&os=macos&arch=$arch" 2>/dev/null)
    if test -z "$json"
        echo "Failed to fetch Zed release metadata." >&2
        return 1
    end

    set -l url (echo "$json" | jq -r '.url // empty')
    if test -z "$url"
        echo "Zed release metadata is missing download URL." >&2
        return 1
    end

    set -g orchard_app_download_url "$url"
    return 0
end

function orchard_after_install_callback
    orchard_cli_wrapper zed cli
end
