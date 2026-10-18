set -g orchard_app_id opencode-desktop
set -g orchard_app_display_name OpenCode
set -g orchard_app_download_type dmg

function orchard_resolve_download_url_callback
    set -l _pattern 'opencode-desktop-mac-arm64\.dmg$'
    if test (uname -m) != arm64
        set _pattern 'opencode-desktop-mac-x64\.dmg$'
    end
    set -g orchard_app_download_url (orchard_fetch_github_release_asset_url "anomalyco/opencode" "$_pattern")
    return $status
end
