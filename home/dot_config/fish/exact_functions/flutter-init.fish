#!/usr/bin/env fish

function flutter-init -a channel
    # If Flutter is already available, just upgrade it.
    if command -sq flutter
        echo "Flutter SDK detected. Running 'flutter upgrade'..."
        flutter --disable-analytics
        flutter upgrade
        return $status
    end

    # Default channel
    if test -z "$channel"
        set channel stable
    end

    switch "$channel"
        case stable beta dev
            # ok
        case '*'
            echo "Invalid channel: $channel (expected stable | beta | dev)" >&2
            return 1
    end

    # Detect platform via fish_platform (chezmoi-rendered 00-fish-platform.fish)
    if not set -q fish_platform
        echo "fish_platform is not set." >&2
        return 1
    end

    set -l platform unknown
    switch $fish_platform
        case darwin
            set platform macos
        case linux wsl
            set platform linux
        case '*'
            echo "Unsupported platform: $fish_platform" >&2
            return 1
    end

    set -l extract_command unzip -q -o
    set -l extract_destination -d "$HOME"
    if test "$platform" = linux
        set extract_command tar -xf
        set extract_destination -C "$HOME"
    end

    for cmd in curl jq $extract_command[1]
        if not command -sq $cmd
            echo "Required command not found: $cmd" >&2
            echo "Please install it and try again." >&2
            return 1
        end
    end

    # Detect architecture
    set -l uname_arch (uname -m)
    set -l target_arch unknown
    switch "$uname_arch"
        case arm64 aarch64
            set target_arch arm64
        case x86_64
            set target_arch x64
        case '*'
            echo "Unsupported architecture: $uname_arch" >&2
            return 1
    end

    set -l manifest_url "https://storage.googleapis.com/flutter_infra_release/releases/releases_$platform.json"
    set -l temp_dir /tmp
    if test -n "$TMPDIR"
        set temp_dir "$TMPDIR"
    end
    set -l manifest_file (mktemp "$temp_dir/flutter-releases.XXXXXX"); or begin
        echo "Failed to create Flutter manifest temporary file." >&2
        return 1
    end

    echo "Fetching Flutter release manifest for $platform..."
    if not curl -fsSL "$manifest_url" -o "$manifest_file"
        echo "Failed to download Flutter release manifest." >&2
        rm -f "$manifest_file"
        return 1
    end

    # Pick latest archive for current arch and channel (single jq pass)
    set -l release_line (jq -r --arg arch "$target_arch" --arg channel "$channel" '
        .releases[]
        | select(.dart_sdk_arch == $arch and .channel == $channel)
        | "\(.archive) \(.version)"
        ' "$manifest_file" | head -n 1)

    set -l base_url (jq -r '.base_url' "$manifest_file")
    rm -f "$manifest_file"

    if test -z "$release_line" -o "$release_line" = "null null"
        echo "Failed to find a $channel release for $platform / $target_arch." >&2
        return 1
    end

    if test -z "$base_url" -o "$base_url" = null
        echo "Failed to read base_url from release manifest." >&2
        return 1
    end

    string split ' ' -- $release_line | read -l archive flutter_version

    set -l url "$base_url/$archive"

    echo "Latest $channel Flutter version: $flutter_version ($platform, $target_arch)"
    echo "Downloading from:"
    echo "  $url"
    echo

    set -l tmp_archive (mktemp "$temp_dir/flutter-sdk.XXXXXX"); or begin
        echo "Failed to create Flutter archive temporary file." >&2
        return 1
    end

    if not curl -fL "$url" -o "$tmp_archive"
        echo "Download failed." >&2
        rm -f "$tmp_archive"
        return 1
    end

    # Archives contain a top-level 'flutter' directory
    if not $extract_command "$tmp_archive" $extract_destination
        echo "Failed to extract Flutter archive." >&2
        rm -f "$tmp_archive"
        return 1
    end

    rm -f "$tmp_archive"

    fish_add_path_if_exists "$HOME/flutter/bin"

    flutter --disable-analytics
end
