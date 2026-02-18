set -g orchard_app_id itermbrowserplugin
set -g orchard_app_display_name "iTerm2 Browser Plugin"
set -g orchard_app_download_type zip
set -g orchard_app_bundle_name "iTermBrowserPlugin.app"

function orchard_resolve_download_url_callback
    set -l page_url "https://iterm2.com/browser-plugin.html"
    set -l html (curl -sL "$page_url")
    set -l url (echo "$html" | grep -oE 'href="(https://[^"]*iTermBrowserPlugin[^"]*\.zip)"' | head -1 | string replace 'href="' '' | string replace '"' '')
    if test -z "$url"
        echo "Could not find download URL on $page_url." >&2
        return 1
    end
    set -g orchard_app_download_url "$url"
    return 0
end
