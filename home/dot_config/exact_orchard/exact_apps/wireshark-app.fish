set -g orchard_app_id wireshark-app
set -g orchard_app_display_name Wireshark
set -g orchard_app_download_type dmg

function orchard_resolve_download_url_callback
    set -l xml (curl -sL "https://www.wireshark.org/update/0/Wireshark/0.0.0/macOS/arm64/en-US/stable.xml" 2>/dev/null)
    set -l app_version (string match -r '<sparkle:shortVersionString>([^<]+)</sparkle:shortVersionString>' $xml | string replace -r '.*<sparkle:shortVersionString>([^<]+)</sparkle:shortVersionString>.*' '$1')
    test -z "$app_version"; and return 1
    set -g orchard_app_download_url "https://www.wireshark.org/download/osx/all-versions/Wireshark%20$app_version.dmg"
    return 0
end
