set -g orchard_app_id rustdesk
set -g orchard_app_display_name RustDesk
set -g orchard_app_download_type dmg

function orchard_resolve_download_url_callback
    set -l pattern 'rustdesk-.*-aarch64\.dmg$'
    if test (uname -m) != arm64
        set pattern 'rustdesk-.*-x86_64\.dmg$'
    end
    set -g orchard_app_download_url (orchard_fetch_github_release_asset_url "rustdesk/rustdesk" "$pattern")
    return $status
end
