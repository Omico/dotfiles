set -g orchard_app_id wireshark-app
set -g orchard_app_display_name Wireshark
set -g orchard_app_download_type dmg

function orchard_resolve_download_url_callback
    set -l _xml (curl -fsSL "https://www.wireshark.org/update/0/Wireshark/0.0.0/macOS/arm64/en-US/stable.xml"); or begin
        echo "Failed to fetch Wireshark update metadata." >&2
        return 1
    end
    set -l _app_version (string match -rg 'sparkle:shortVersionString="([^"]+)"' -- $_xml)
    if test (count $_app_version) -ne 1; or not string match -qr '^[0-9]+(\.[0-9]+)+$' -- "$_app_version"
        echo "Failed to resolve the Wireshark version." >&2
        return 1
    end
    set -g orchard_app_download_url "https://www.wireshark.org/download/osx/all-versions/Wireshark%20$_app_version.dmg"
    return 0
end
