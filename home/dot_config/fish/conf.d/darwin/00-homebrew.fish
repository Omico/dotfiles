#/usr/bin/env fish

if test -x /opt/homebrew/bin/brew
    export HOMEBREW_NO_ANALYTICS=1
    eval (/opt/homebrew/bin/brew shellenv)
end

# Android SDK
fish_add_android_sdk_root /opt/homebrew/share/android-commandlinetools

# Zip & Unzip
fish_add_path_if_exists /opt/homebrew/opt/zip/bin /opt/homebrew/opt/unzip/bin
