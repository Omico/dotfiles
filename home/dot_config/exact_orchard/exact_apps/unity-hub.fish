set -g orchard_app_id unity-hub
set -g orchard_app_display_name "Unity Hub"
set -g orchard_app_download_type dmg

function orchard_resolve_download_url_callback
    set -l arch x64
    if test (uname -m) = arm64
        set arch arm64
    end
    set -g orchard_app_download_url "https://public-cdn.cloud.unity3d.com/hub/prod/UnityHubSetup-$arch.dmg"
    echo "Unity Hub download URL: $orchard_app_download_url"
    return 0
end
