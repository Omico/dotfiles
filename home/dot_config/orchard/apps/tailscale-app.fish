set -g orchard_app_id tailscale-app
set -g orchard_app_display_name Tailscale
set -g orchard_app_download_url "https://pkgs.tailscale.com/stable/Tailscale-latest-macos.pkg"
set -g orchard_app_download_type pkg

function orchard_after_install_callback
    orchard_cli_wrapper tailscale Tailscale
end
