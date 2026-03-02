set -g orchard_app_id jetbrains-toolbox
set -g orchard_app_display_name "JetBrains Toolbox"
set -g orchard_app_download_type dmg

function orchard_resolve_download_url_callback
    set -l json (curl -fsSL "https://data.services.jetbrains.com/products/releases?code=TBA&latest=true&type=release" 2>/dev/null)
    if test -z "$json"
        echo "Failed to fetch JetBrains Toolbox release metadata." >&2
        return 1
    end

    set -l key mac
    if test "$(uname -m)" = arm64
        set key macM1
    end

    set -l url (echo "$json" | jq -r --arg key "$key" '."TBA"[0].downloads[$key].link // empty')

    if test -z "$url" -o "$url" = null
        echo "JetBrains Toolbox release metadata is missing download URL for macOS." >&2
        return 1
    end

    set -g orchard_app_download_url "$url"
    return 0
end
