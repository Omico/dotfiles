on run arguments
    set themeFile to POSIX file (item 1 of arguments)
    set themeName to "My"
    tell application id "com.apple.Terminal"
        set initialWindows to id of every window
        if exists settings set themeName then
            delete settings set themeName
        end if

        open themeFile
        repeat 50 times
            if exists settings set themeName then exit repeat
            delay 0.1
        end repeat
        if not (exists settings set themeName) then
            error "Failed to import the My Terminal theme."
        end if
        set default settings to settings set themeName

        set openedWindows to id of every window
        repeat with windowID in openedWindows
            if initialWindows contains (contents of windowID) then
                set current settings of tabs of (every window whose id is windowID) to settings set themeName
            else
                close (every window whose id is windowID)
            end if
        end repeat
    end tell
end run
