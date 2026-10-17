set -g orchard_app_id kim
set -g orchard_app_display_name Kim
set -g orchard_app_download_type dmg

function orchard_resolve_download_url_callback
    set -l api_type darwin
    if test (uname -m) = arm64
        set api_type darwin-arm
    end
    set -l api_url "https://kim.kuaishou.com/mis/deploy/version/v2/appDownloadUrl?type=$api_type"
    set -l json (curl -sL "$api_url" 2>/dev/null)
    if test -z "$json"
        echo "Failed to fetch Kim download URL from API." >&2
        return 1
    end
    set -l url (echo "$json" | jq -r '.data.format // empty' 2>/dev/null)
    if test -z "$url"
        echo "Could not parse download URL from Kim API response." >&2
        return 1
    end
    set -g orchard_app_download_url "$url"
    return 0
end
