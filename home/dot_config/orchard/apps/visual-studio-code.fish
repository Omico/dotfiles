set -g orchard_app_id visual-studio-code
set -g orchard_app_display_name "Visual Studio Code"
set -g orchard_app_download_url "https://code.visualstudio.com/sha/download?build=stable&os=darwin-universal-dmg"
set -g orchard_app_download_type dmg

function orchard_after_install_callback
    _orchard_cli_symlink code Contents/Resources/app/bin/code
end
