set -g orchard_app_id gitkraken
set -g orchard_app_display_name GitKraken
set -g orchard_app_download_type zip

function orchard_resolve_download_url_callback
    set -l arch arm64
    set -l livecheck_arch -arm64
    if test (uname -m) != arm64
        set arch x64
        set livecheck_arch ""
    end

    set -l json (curl -sL "https://release.gitkraken.com/darwin$livecheck_arch/RELEASES" 2>/dev/null)
    set -l app_version (echo "$json" | jq -r '.name' 2>/dev/null)
    test -z "$app_version"; and return 1

    set -g orchard_app_download_url "https://api.gitkraken.dev/releases/production/darwin/$arch/$app_version/GitKraken-v$app_version.zip"
    return 0
end
