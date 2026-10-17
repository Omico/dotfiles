set -g orchard_app_id iina
set -g orchard_app_display_name IINA
set -g orchard_app_download_type dmg

function orchard_resolve_download_url_callback
    set -g orchard_app_download_url (orchard_fetch_github_release_asset_url "iina/iina" '^IINA\.v.*\.dmg$')
    return $status
end

function orchard_after_install_callback
    orchard_cli_wrapper iina iina-cli
end
