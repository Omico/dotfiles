set -g orchard_app_id ghostty
set -g orchard_app_display_name Ghostty
set -g orchard_app_download_type dmg

function orchard_resolve_download_url_callback
    set -l _sparkle_feed_url "https://release.files.ghostty.org/appcast.xml"
    set -l _release_dmg_xpath "string((//*[local-name()='enclosure'][contains(@url,'Ghostty.dmg')])[last()]/@url)"

    set -l _sparkle_xml (curl -fsSL "$_sparkle_feed_url" 2>/dev/null)
    test -n "$_sparkle_xml"; or begin
        echo "Failed to fetch Ghostty Sparkle appcast." >&2
        return 1
    end

    set -l _raw_dmg_url (printf '%s' "$_sparkle_xml" | xmllint --xpath "$_release_dmg_xpath" - 2>/dev/null)
    set -l _dmg_url (string trim -- $_raw_dmg_url)
    test -n "$_dmg_url"; or begin
        echo "Failed to parse Ghostty.dmg URL from appcast (xmllint)." >&2
        return 1
    end

    set -g orchard_app_download_url "$_dmg_url"
    return 0
end

function orchard_after_install_callback
    orchard_cli_wrapper ghostty
end
