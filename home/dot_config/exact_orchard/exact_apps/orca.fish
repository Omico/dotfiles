set -g orchard_app_id orca
set -g orchard_app_display_name Orca
set -g orchard_app_download_type dmg

function orchard_resolve_download_url_callback
    set -l pattern 'orca-macos-arm64\.dmg$'
    if test (uname -m) != arm64
        set pattern 'orca-macos-x64\.dmg$'
    end
    set -g orchard_app_download_url (orchard_fetch_github_release_asset_url "stablyai/orca" "$pattern")
    return $status
end

function orchard_after_install_callback
    orchard_cli_symlink orca Contents/Resources/bin/orca
end
