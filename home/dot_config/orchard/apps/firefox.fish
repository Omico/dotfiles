set -g orchard_app_id firefox
set -g orchard_app_display_name Firefox
set -g orchard_app_download_url "https://download.mozilla.org/?product=firefox-latest-ssl&os=osx"
set -g orchard_app_download_type dmg

function orchard_after_install_callback
    orchard_cli_wrapper firefox
end
