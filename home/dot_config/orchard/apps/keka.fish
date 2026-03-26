set -g orchard_app_id keka
set -g orchard_app_display_name Keka
set -g orchard_app_download_type dmg

function orchard_resolve_download_url_callback
    set -g orchard_app_download_url (orchard_fetch_github_release_asset_url "aonez/Keka" 'Keka-.*\.dmg$')
    return $status
end

function orchard_after_install_callback
    orchard_cli_wrapper keka Keka --cli
end
