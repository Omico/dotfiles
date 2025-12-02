#/usr/bin/env fish

if test -x /opt/homebrew/bin/brew
    export HOMEBREW_NO_ANALYTICS=1
    eval (/opt/homebrew/bin/brew shellenv)
end

# Android SDK
if test -d /opt/homebrew/share/android-commandlinetools
    set -gx ANDROID_SDK_ROOT /opt/homebrew/share/android-commandlinetools
    # For legacy reasons, some tools expect ANDROID_HOME to be set
    set -gx ANDROID_HOME $ANDROID_SDK_ROOT
    fish_add_path $ANDROID_SDK_ROOT/platform-tools
end

# Zip
if test -d /opt/homebrew/opt/zip/bin
    fish_add_path /opt/homebrew/opt/zip/bin
end

# Unzip
if test -d /opt/homebrew/opt/unzip/bin
    fish_add_path /opt/homebrew/opt/unzip/bin
end
