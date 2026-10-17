set -g orchard_app_id nomachine
set -g orchard_app_display_name NoMachine
set -g orchard_app_download_type dmg
set -g orchard_app_pkg_name "NoMachine.pkg"

function orchard_resolve_download_url_callback
    set -l page_url "https://download.nomachine.com/download/?id=7&platform=mac"
    set -l html (curl -fsSL "$page_url" 2>/dev/null)
    if test -z "$html"
        echo "Failed to fetch NoMachine download page." >&2
        return 1
    end

    set -l match (string match -r 'id="link_download" href="(https://[^"]+\.dmg)"' -- $html)
    if test -z "$match"
        echo "Could not find macOS download URL on NoMachine page." >&2
        return 1
    end

    set -g orchard_app_download_url "$match[2]"
    return 0
end
