#!/usr/bin/env fish

set -g __gnome_keyring_login_collection /org/freedesktop/secrets/collection/login
set -g __gnome_keyring_default_keyring "$HOME/.local/share/keyrings/default.keyring"

function gnome-keyring-status --description 'Check whether GNOME login keyring is locked'
    set -l quiet false

    switch "$argv[1]"
        case --quiet -q
            set quiet true
            set -e argv[1]
    end

    if test (count $argv) -gt 0
        printf "Usage: %s [--quiet]\n" (status function) >&2
        return 2
    end

    __ensure_user_dbus_env; or return 1
    __gnome_keyring_require_commands timeout busctl; or return 1
    __gnome_keyring_check_problem_default_keyring $quiet; or return 1

    set -l locked (__gnome_keyring_login_keyring_locked); or return 1
    if test "$locked" = true
        if test "$quiet" != true
            echo "GNOME login keyring: locked"
            echo "Run gnome-keyring-unlock to unlock it for this shell." >&2
        end
        return 1
    end

    if test "$quiet" != true
        echo "GNOME login keyring: unlocked"
    end
end

function gnome-keyring-restart --description 'Restart GNOME keyring Secret Service for current user'
    __ensure_user_dbus_env; or return 1
    __gnome_keyring_require_commands timeout gnome-keyring-daemon; or return 1
    __gnome_keyring_delete_problem_default_keyring false; or return 1
    __gnome_keyring_kill_stuck_secret_tool; or return 1
    __gnome_keyring_restart_secret_service; or return 1
end

function gnome-keyring-unlock --description 'Unlock GNOME login keyring for current user session'
    __ensure_user_dbus_env; or return 1
    __gnome_keyring_require_commands timeout gnome-keyring-daemon busctl; or return 1
    __gnome_keyring_delete_problem_default_keyring false; or return 1
    __gnome_keyring_restart_secret_service; or return 1

    set -l locked (__gnome_keyring_login_keyring_locked); or return 1
    if test "$locked" = false
        echo "GNOME login keyring is already unlocked."
        return 0
    end

    if not isatty stdin
        echo "Run this from an interactive shell so the GNOME keyring password can be read safely." >&2
        return 1
    end

    echo "GNOME login keyring is locked; unlocking."

    set -l keyring_password
    read --silent --prompt-str "Ubuntu login password: " keyring_password
    set -l read_status $status
    echo

    if test $read_status -ne 0
        echo "Keyring password prompt was cancelled." >&2
        return 1
    end
    if test -z "$keyring_password"
        echo "Empty password, abort." >&2
        return 1
    end

    printf "%s" "$keyring_password" | gnome-keyring-daemon --unlock --components=secrets
    set -l unlock_status $status

    set -e keyring_password

    if test $unlock_status -ne 0
        __gnome_keyring_report_status "gnome-keyring-daemon --unlock" $unlock_status
        return $unlock_status
    end

    __gnome_keyring_restart_secret_service; or return 1
    gnome-keyring-status
end

function __gnome_keyring_restart_secret_service --description 'internal: restart GNOME keyring Secret Service'
    if command -q systemctl
        __gnome_keyring_timeout 10s systemctl --user restart gnome-keyring-daemon.service 2>/dev/null
        or true
        __gnome_keyring_timeout 10s systemctl --user restart gnome-keyring-daemon.socket 2>/dev/null
        or true
    end
end

function __gnome_keyring_kill_stuck_secret_tool --description 'internal: kill stuck secret-tool processes for current user'
    __gnome_keyring_require_commands timeout pkill whoami; or return 1

    set -l username (__gnome_keyring_capture whoami 5s whoami); or return 1
    if test -z "$username"
        echo "whoami returned an empty username." >&2
        return 1
    end

    __gnome_keyring_timeout 5s pkill -u "$username" -x secret-tool 2>/dev/null
    or true
end

function __gnome_keyring_check_problem_default_keyring --description 'internal: detect default.keyring when it is known to break unlock'
    set -l quiet $argv[1]

    if not test -e "$__gnome_keyring_default_keyring"
        return 0
    end

    if test "$quiet" != true
        printf "Problematic keyring file exists: %s\n" "$__gnome_keyring_default_keyring" >&2
        echo "A stale or invalid default.keyring can keep the login keyring locked even when unlock exits successfully." >&2
        echo "Run gnome-keyring-unlock or gnome-keyring-restart to delete it automatically." >&2
    end

    return 1
end

function __gnome_keyring_delete_problem_default_keyring --description 'internal: delete default.keyring when it is known to break unlock'
    set -l quiet $argv[1]

    if not test -e "$__gnome_keyring_default_keyring"
        return 0
    end

    __gnome_keyring_require_commands rm; or return 1
    rm -f "$__gnome_keyring_default_keyring"; or return 1

    if test "$quiet" != true
        printf "Deleted problematic keyring file: %s\n" "$__gnome_keyring_default_keyring"
    end
end

function __gnome_keyring_start_secret_service --description 'internal: initialize GNOME keyring Secret Service'
    if command -q systemctl
        systemctl --user start gnome-keyring-daemon.socket 2>/dev/null
        or true
    end

    for line in (gnome-keyring-daemon --start --components=secrets 2>/dev/null)
        if string match -q '*=*' -- $line
            set -l key_value (string split -m1 = -- $line)
            if test (count $key_value) -eq 2
                set -gx $key_value[1] $key_value[2]
            end
        end
    end
end

function __gnome_keyring_require_commands --description 'internal: check GNOME keyring helper dependencies'
    set -l missing
    for name in $argv
        command -q $name; or set -a missing $name
    end

    if not set -q missing[1]
        return 0
    end

    printf "Missing command(s): %s\n" (string join ", " $missing) >&2
    echo "Install Ubuntu GNOME dependencies such as gnome-keyring, libsecret-tools, systemd, procps, and coreutils." >&2
    return 1
end

function __gnome_keyring_login_keyring_locked --description 'internal: print true when the GNOME login keyring is locked'
    set -l locked_result (__gnome_keyring_capture "GNOME login keyring lock check" 5s busctl --user get-property \
        org.freedesktop.secrets \
        $__gnome_keyring_login_collection \
        org.freedesktop.Secret.Collection Locked); or return 1

    if string match -q -r '^b true$' -- "$locked_result"
        echo true
        return 0
    end
    if string match -q -r '^b false$' -- "$locked_result"
        echo false
        return 0
    end

    printf "Could not parse GNOME login keyring lock state: %s\n" "$locked_result" >&2
    return 1
end

function __gnome_keyring_timeout --description 'internal: run a command with a short timeout'
    set -l seconds $argv[1]
    set -e argv[1]

    if test -z "$seconds"; or test (count $argv) -eq 0
        echo "__gnome_keyring_timeout: expected seconds and command." >&2
        return 2
    end
    if not command -q timeout
        echo "timeout: command not found; install coreutils." >&2
        return 127
    end

    command timeout --foreground --kill-after=2s "$seconds" $argv
end

function __gnome_keyring_capture --description 'internal: run a command with timeout and print captured output'
    set -l label $argv[1]
    set -l seconds $argv[2]
    set -e argv[1 2]

    if test -z "$label"; or test -z "$seconds"; or test (count $argv) -eq 0
        echo "__gnome_keyring_capture: expected label, seconds, and command." >&2
        return 2
    end

    set -l output (__gnome_keyring_timeout "$seconds" $argv 2>/dev/null)
    set -l command_status $status
    if test $command_status -ne 0
        __gnome_keyring_report_status "$label" $command_status
        return $command_status
    end

    printf "%s\n" $output
end

function __gnome_keyring_report_status --description 'internal: print a concise command failure'
    set -l label $argv[1]
    set -l code $argv[2]

    switch $code
        case 124
            printf "%s timed out.\n" "$label" >&2
        case 137
            printf "%s was killed after timing out.\n" "$label" >&2
        case 127
            printf "%s could not run because a command is missing.\n" "$label" >&2
        case '*'
            printf "%s exited with status %s.\n" "$label" "$code" >&2
    end
end
