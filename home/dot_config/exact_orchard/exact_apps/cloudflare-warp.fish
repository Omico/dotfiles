set -g orchard_app_id cloudflare-warp
set -g orchard_app_display_name "Cloudflare WARP"
set -g orchard_app_download_type pkg

function orchard_resolve_download_url_callback
    set -l xml (curl -sL "https://downloads.cloudflareclient.com/v1/update/sparkle/macos/ga" 2>/dev/null)
    set -l matches (string match -r 'url=\"([^\"]+Cloudflare_WARP_[^\"]+\\.pkg)\"' $xml)
    test (count $matches) -eq 0; and return 1
    set -l app_url (string replace -r '.*url=\"([^\"]+)\".*' '$1' -- $matches[1])
    test -z "$app_url"; and return 1
    set -g orchard_app_download_url $app_url
    return 0
end
