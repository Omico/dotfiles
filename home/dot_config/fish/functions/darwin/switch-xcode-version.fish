#!/usr/bin/env fish

function switch-xcode-version --description "Switch between different Xcode versions"
    set -l __xcode_app "/Applications/Xcode.app"
    set -l __xcode_versions

    # Check if /Applications/Xcode.app exists and is not a symlink
    if test -d "$__xcode_app" -a ! -L "$__xcode_app"
        echo "❌ Error: $__xcode_app already exists and is not a symlink. Aborting to avoid overwriting the real app."
        return 1
    end

    # Show current Xcode version if available
    if test -L "$__xcode_app"
        set -l __current_target (readlink "$__xcode_app")
        if test -n "$__current_target"
            set -l __current_name (basename "$__current_target")
            echo "📍 Current Xcode: $__current_name"
            echo ""
        end
    else if test -d "$__xcode_app"
        set -l __current_version (/usr/libexec/PlistBuddy -c "Print :CFBundleShortVersionString" "$__xcode_app/Contents/Info.plist" 2>/dev/null)
        if test -n "$__current_version"
            echo "📍 Current Xcode: Xcode.app (version $__current_version)"
            echo ""
        end
    end

    # Find all Xcode versions
    for __xcode in /Applications/Xcode_*.app
        if test -d "$__xcode"
            # Verify this is a real Xcode app
            # Check for Contents/Developer directory and correct bundle identifier
            if test -d "$__xcode/Contents/Developer"
                set -l __bundle_id (/usr/libexec/PlistBuddy -c "Print :CFBundleIdentifier" "$__xcode/Contents/Info.plist" 2>/dev/null)
                if test "$__bundle_id" = "com.apple.dt.Xcode"
                    set -a __xcode_versions "$__xcode"
                end
            end
        end
    end

    # Check if any versions were found
    if test (count $__xcode_versions) -eq 0
        echo "❌ No Xcode versions found"
        return 1
    end

    # Auto-select if only one version found
    set -l __selected_xcode
    set -l __selected_name
    if test (count $__xcode_versions) -eq 1
        set __selected_xcode $__xcode_versions[1]
        set __selected_name (basename "$__selected_xcode")
        echo "📱 Found single Xcode version: $__selected_name"
        echo ""
    else
        # List all available Xcode versions
        echo "📱 Available Xcode versions:"
        set -l __xcode_index 1
        for __xcode in $__xcode_versions
            set -l __xcode_name (basename "$__xcode")
            set -l __xcode_version (/usr/libexec/PlistBuddy -c "Print :CFBundleShortVersionString" "$__xcode/Contents/Info.plist" 2>/dev/null)
            if test -n "$__xcode_version"
                echo "  $__xcode_index. $__xcode_name (version $__xcode_version)"
            else
                echo "  $__xcode_index. $__xcode_name"
            end
            set __xcode_index (math $__xcode_index + 1)
        end

        # Prompt user to select
        echo ""
        read -P "Select version to switch to (1-"(count $__xcode_versions)"): " __choice

        # Handle empty input (user cancelled)
        if test -z "$__choice"
            echo "❌ Cancelled"
            return 1
        end

        # Validate input
        if not string match -qr '^[0-9]+$' "$__choice"
            echo "❌ Invalid selection: must be a number"
            return 1
        end
        if test "$__choice" -lt 1 -o "$__choice" -gt (count $__xcode_versions)
            echo "❌ Invalid selection: out of range"
            return 1
        end

        # Get selected Xcode version
        set __selected_xcode $__xcode_versions[$__choice]
        set __selected_name (basename "$__selected_xcode")
    end

    # Check if already pointing to selected version
    if test -L "$__xcode_app"
        set -l __current_target (readlink "$__xcode_app")
        # Normalize current target to absolute path if it's relative
        if string match -qv '/*' "$__current_target"
            # Relative symlink: resolve relative to /Applications
            set -l __resolved_target "/Applications/$__current_target"
            if test -d "$__resolved_target"
                set __current_target "$__resolved_target"
            end
        end
        # Compare paths
        if test "$__current_target" = "$__selected_xcode"
            echo "✅ Already using $__selected_name"
            return 0
        end
    end

    echo "🔗 Linking to: $__selected_xcode"

    # Execute link operation
    if not sudo ln -sfn "$__selected_xcode" "$__xcode_app"
        echo "❌ Failed to create symlink"
        return 1
    end

    # Execute switch operation
    if not sudo xcode-select -switch "$__xcode_app/Contents/Developer"
        echo "❌ Failed to switch xcode-select"
        return 1
    end

    echo "✅ Successfully switched to $__selected_name"

    # Accept Xcode license
    echo "📜 Accepting Xcode license..."
    if sudo xcodebuild -license accept
        echo "✅ License accepted"
    else
        echo "⚠️  Failed to accept license (may require manual acceptance)"
    end
end
