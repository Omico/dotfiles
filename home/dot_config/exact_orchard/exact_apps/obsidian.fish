set -g orchard_app_id obsidian
set -g orchard_app_display_name Obsidian
set -g orchard_app_download_type dmg

function orchard_resolve_download_url_callback
    set -g orchard_app_download_url (orchard_fetch_github_release_asset_url "obsidianmd/obsidian-releases" '^Obsidian-[0-9]+\.[0-9]+\.[0-9]+\.dmg$')
    return $status
end

function orchard_after_install_callback
    orchard_cli_wrapper obsidian obsidian-cli
end
