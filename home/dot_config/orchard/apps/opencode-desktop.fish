set -g orchard_app_id opencode-desktop
set -g orchard_app_display_name OpenCode
set -g orchard_app_download_type dmg

function orchard_resolve_download_url_callback
    set -l pattern 'opencode-desktop-darwin-aarch64\.dmg$'
    if test (uname -m) != arm64
        set pattern 'opencode-desktop-darwin-x64\.dmg$'
    end
    set -g orchard_app_download_url (orchard_fetch_github_release_asset_url "sst/opencode" "$pattern")
    return $status
end
