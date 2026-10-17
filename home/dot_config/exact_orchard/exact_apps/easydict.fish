set -g orchard_app_id easydict
set -g orchard_app_display_name Easydict
set -g orchard_app_download_type dmg

function orchard_resolve_download_url_callback
    set -g orchard_app_download_url (orchard_fetch_github_release_asset_url "tisfeng/Easydict" '^Easydict\.dmg$')
    return $status
end
