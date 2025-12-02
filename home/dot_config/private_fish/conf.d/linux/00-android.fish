#!/usr/bin/env fish

if test -d $HOME/Android/Sdk
    set -gx ANDROID_HOME $HOME/Android/Sdk
    set -gx ANDROID_SDK_ROOT $ANDROID_HOME
end
