set -g orchard_app_id cursor
set -g orchard_app_display_name Cursor
set -g orchard_app_download_url "https://api2.cursor.sh/updates/download/golden/darwin-universal/cursor/latest"
set -g orchard_app_download_type dmg

function orchard_after_install_callback
    orchard_cli_symlink cursor Contents/Resources/app/bin/cursor
end
