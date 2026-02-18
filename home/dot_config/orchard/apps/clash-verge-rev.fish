set -g orchard_app_id clash-verge-rev
set -g orchard_app_display_name "Clash Verge Rev"
set -g orchard_app_download_type dmg
set -g orchard_app_bundle_name "Clash Verge.app"

function orchard_resolve_download_url_callback
    set -l pattern 'Clash\.Verge_.*_aarch64\.dmg$'
    if test (uname -m) != arm64
        set pattern 'Clash\.Verge_.*_x64\.dmg$'
    end
    set -g orchard_app_download_url (orchard_fetch_github_release_asset_url "clash-verge-rev/clash-verge-rev" "$pattern")
    return $status
end
