set -g orchard_app_id ollama-app
set -g orchard_app_display_name Ollama
set -g orchard_app_download_url "https://ollama.com/download/Ollama.dmg"
set -g orchard_app_download_type dmg

function orchard_after_install_callback
    _orchard_cli_symlink ollama Contents/Resources/ollama
end
