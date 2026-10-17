set -g orchard_app_id codexbar
set -g orchard_app_display_name CodexBar
set -g orchard_app_download_type zip

function orchard_resolve_download_url_callback
    set -g orchard_app_download_url (orchard_fetch_github_release_asset_url "steipete/CodexBar" '^CodexBar-macos-universal-[0-9]+\.[0-9]+\.[0-9]+\.zip$')
    return $status
end

function orchard_after_install_callback
    orchard_cli_symlink codexbar Contents/Helpers/CodexBarCLI
end
