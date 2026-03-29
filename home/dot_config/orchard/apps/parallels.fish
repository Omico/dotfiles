set -g orchard_app_id parallels
set -g orchard_app_display_name "Parallels Desktop"
set -g orchard_app_download_type dmg

function orchard_resolve_download_url_callback
    set -l _website_links_base https://download.parallels.com/website_links
    set -l _index_json (curl -sfL "$_website_links_base/desktop/index.json" 2>/dev/null)
    if test -z "$_index_json"
        echo "parallels: failed to fetch desktop version index" >&2
        return 1
    end
    set -l _major_version (echo "$_index_json" | jq -r 'to_entries | max_by(.key | tonumber) | .key')
    if test -z "$_major_version"; or test "$_major_version" = null
        echo "parallels: could not determine max version key from desktop index" >&2
        return 1
    end
    set -g orchard_app_download_url "https://link.parallels.com/pdfm/v$_major_version/dmg-download"
    return 0
end

function orchard_after_install_callback
    chflags nohidden "$orchard_app_bundle_path" 2>/dev/null
    xattr -d com.apple.FinderInfo "$orchard_app_bundle_path" 2>/dev/null
end
