set -g orchard_app_id bricklink-studio
set -g orchard_app_display_name "BrickLink Studio"
set -g orchard_app_download_type pkg

function orchard_resolve_download_url_callback
    set -l html (curl -sL "https://www.bricklink.com/v3/studio/download.page" 2>/dev/null)
    set -l studio_version (string match -r '"strVersion"\s*:\s*"([^"]+)"' $html | string replace -r '.*"([^"]+)"$' '$1')
    test -z "$studio_version"; and return 1
    set -g orchard_app_download_url "https://studio.download.bricklink.info/Studio2.0/Archive/$studio_version/Studio+2.0.pkg"
    return 0
end
