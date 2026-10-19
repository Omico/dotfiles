#!/usr/bin/env fish

if test -x /opt/homebrew/bin/brew
    eval (/opt/homebrew/bin/brew shellenv)
end

# Zip & Unzip
fish_add_path_if_exists /opt/homebrew/opt/zip/bin /opt/homebrew/opt/unzip/bin
