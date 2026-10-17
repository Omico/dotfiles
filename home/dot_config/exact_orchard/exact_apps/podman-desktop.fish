set -g orchard_app_id podman-desktop
set -g orchard_app_display_name "Podman Desktop"
set -g orchard_app_download_type dmg

function orchard_resolve_download_url_callback
    set -l pattern 'podman-desktop-.*-arm64\.dmg$'
    if test (uname -m) != arm64
        set pattern 'podman-desktop-.*-x64\.dmg$'
    end
    set -g orchard_app_download_url (orchard_fetch_github_release_asset_url "containers/podman-desktop" "$pattern")
    return $status
end
