set -g orchard_app_id beyond-compare
set -g orchard_app_display_name "Beyond Compare"
set -g orchard_app_download_type zip

function orchard_resolve_download_url_callback
    set -l html (curl -sL "https://www.scootersoftware.com/download" 2>/dev/null)
    if test -z "$html"
        echo "Failed to fetch Beyond Compare download page." >&2
        return 1
    end

    set -l match (string match -r 'href="(/files/BCompareOSX-[0-9]+(?:\.[0-9]+)+\.zip)"' -- $html)
    if test -z "$match"
        echo "Could not find macOS download URL on Beyond Compare page." >&2
        return 1
    end

    set -l rel_path "$match[2]"
    set -g orchard_app_download_url "https://www.scootersoftware.com$rel_path"
    return 0
end

function orchard_after_install_callback
    _orchard_cli_symlink bcomp Contents/MacOS/bcomp
end
