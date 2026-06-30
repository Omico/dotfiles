#!/usr/bin/env fish

set -g __grd_rdp_schema org.gnome.RemoteDesktop.RdpCredentials
set -g __grd_rdp_label "GNOME Remote Desktop RDP credentials"
set -g __grd_rdp_service gnome-remote-desktop.service

function grd-rdp-status --description 'Show GNOME Remote Desktop RDP status'
    __ensure_user_dbus_env; or return 1

    set -l command_status 0

    echo "GNOME Remote Desktop RDP"
    printf "  service: %s\n" "$__grd_rdp_service"
    printf "  port:    %s\n" 3389

    if command -q grdctl
        __grd_rdp_status_command grdctl 5s "grdctl status" grdctl status; or set command_status 1
    else
        __grd_rdp_status_missing_command grdctl grdctl
        set command_status 1
    end

    if command -q systemctl
        __grd_rdp_status_command "User service" 5s "systemctl --user status $__grd_rdp_service --no-pager" systemctl --user status $__grd_rdp_service --no-pager; or set command_status 1
    else
        __grd_rdp_status_missing_command "User service" systemctl
        set command_status 1
    end

    __grd_rdp_status_heading "TCP listener"
    __grd_rdp_port_status
    or set command_status 1

    return $command_status
end

function grd-rdp-set-credentials --description 'Set GNOME Remote Desktop RDP credentials via Secret Service'
    if test (count $argv) -gt 1
        printf "Usage: %s [username]\n" (status function) >&2
        return 2
    end

    __ensure_user_dbus_env; or return 1
    __grd_rdp_require_commands timeout secret-tool grdctl systemctl; or return 1
    functions -q gnome-keyring-status; or begin
        echo "gnome-keyring-status is not loaded." >&2
        return 1
    end
    gnome-keyring-status --quiet; or begin
        echo "GNOME login keyring is locked or unavailable; run gnome-keyring-unlock first." >&2
        return 1
    end

    set -l rdp_username $argv[1]
    if test -z "$rdp_username"
        set -l default_username (__grd_rdp_current_username); or return 1

        read --prompt-str "RDP username [$default_username]: " rdp_username
        if test -z "$rdp_username"
            set rdp_username "$default_username"
        end
    end

    if not isatty stdin
        echo "Run this from an interactive shell so the RDP password can be read safely." >&2
        return 1
    end

    set -l rdp_password
    read --silent --prompt-str "RDP password: " rdp_password
    set -l read_status $status
    echo

    if test $read_status -ne 0
        echo "RDP password prompt was cancelled." >&2
        return 1
    end
    if test -z "$rdp_password"
        echo "Empty password, abort." >&2
        return 1
    end

    set -l escaped_username (__grd_rdp_gvariant_string "$rdp_username")
    set -l variant_status $status
    if test $variant_status -ne 0
        set -e rdp_password
        return 1
    end

    set -l escaped_password (__grd_rdp_gvariant_string "$rdp_password")
    set variant_status $status
    set -e rdp_password
    if test $variant_status -ne 0
        return 1
    end

    set -l secret (printf "{'username': <%s>, 'password': <%s>}" "$escaped_username" "$escaped_password")
    set -e escaped_password

    printf "%s" "$secret" | __grd_rdp_timeout 5s secret-tool store \
        --label "$__grd_rdp_label" \
        xdg:schema $__grd_rdp_schema
    set -l store_status $status
    set -e secret

    if test $store_status -ne 0
        echo
        __grd_rdp_report_status "secret-tool store $__grd_rdp_schema" $store_status
        echo "Try:" >&2
        echo "  gnome-keyring-unlock" >&2
        printf "  grd-rdp-set-credentials %s\n" (string escape -- "$rdp_username") >&2
        return $store_status
    end

    __grd_rdp_run 15s "grdctl rdp enable" grdctl rdp enable; or return 1

    __grd_rdp_timeout 15s grdctl rdp disable-view-only
    set -l view_only_status $status
    if test $view_only_status -ne 0
        __grd_rdp_report_status "grdctl rdp disable-view-only" $view_only_status
    end

    grd-rdp-restart; or return 1

    echo
    __grd_rdp_timeout 10s grdctl status
end

function grd-rdp-restart --description 'Restart the GNOME Remote Desktop user service'
    __ensure_user_dbus_env; or return 1
    __grd_rdp_require_commands timeout systemctl; or return 1

    __grd_rdp_run 20s "systemctl --user restart $__grd_rdp_service" systemctl --user restart $__grd_rdp_service; or return 1

    printf "Restarted %s.\n" "$__grd_rdp_service"
end

function grd-rdp-fix --description 'Common flow: unlock GNOME keyring, set RDP credentials, restart GRD'
    if test (count $argv) -gt 1
        printf "Usage: %s [username]\n" (status function) >&2
        return 2
    end

    __grd_rdp_kill_stuck; or return 1
    gnome-keyring-unlock; or return 1
    grd-rdp-set-credentials $argv
end

function __grd_rdp_kill_stuck --description 'internal: kill stuck secret-tool and grdctl processes for current user'
    __ensure_user_dbus_env; or return 1
    __grd_rdp_require_commands timeout pkill whoami; or return 1

    set -l username (__grd_rdp_current_username); or return 1

    __grd_rdp_timeout 5s pkill -u "$username" -x secret-tool 2>/dev/null
    or true

    __grd_rdp_timeout 5s pkill -u "$username" -x grdctl 2>/dev/null
    or true

    echo "Killed stuck secret-tool/grdctl if any."
end

function __grd_rdp_require_commands --description 'internal: check Ubuntu GNOME helper dependencies'
    set -l missing
    for name in $argv
        command -q $name; or set -a missing $name
    end

    if not set -q missing[1]
        return 0
    end

    printf "Missing command(s): %s\n" (string join ", " $missing) >&2
    echo "Install Ubuntu GNOME dependencies such as gnome-remote-desktop, libsecret-tools, gnome-keyring, systemd, iproute2, procps, and coreutils." >&2
    return 1
end

function __grd_rdp_timeout --description 'internal: run a command with a short timeout'
    set -l seconds $argv[1]
    set -e argv[1]

    if test -z "$seconds" -o (count $argv) -eq 0
        echo "__grd_rdp_timeout: expected seconds and command." >&2
        return 2
    end
    if not command -q timeout
        echo "timeout: command not found; install coreutils." >&2
        return 127
    end

    command timeout --foreground --kill-after=2s "$seconds" $argv
end

function __grd_rdp_current_username --description 'internal: print the current username'
    set -l username (__grd_rdp_timeout 5s whoami)
    set -l user_status $status
    if test $user_status -ne 0
        __grd_rdp_report_status whoami $user_status
        return $user_status
    end
    if test -z "$username"
        echo "whoami returned an empty username." >&2
        return 1
    end

    printf "%s\n" "$username"
end

function __grd_rdp_run --description 'internal: run a timed command and report non-zero exits'
    set -l seconds $argv[1]
    set -l label $argv[2]
    set -e argv[1 2]

    __grd_rdp_timeout "$seconds" $argv
    set -l command_status $status
    if test $command_status -ne 0
        __grd_rdp_report_status "$label" $command_status
    end

    return $command_status
end

function __grd_rdp_status_heading --description 'internal: print a grd-rdp-status section heading'
    set -l title $argv[1]

    echo
    printf "[%s]\n" "$title"
end

function __grd_rdp_print_indented --description 'internal: print command output indented for status blocks'
    if not set -q argv[1]
        echo "    (no output)"
        return
    end

    for line in $argv
        printf "    %s\n" "$line"
    end
end

function __grd_rdp_status_missing_command --description 'internal: print a missing command status block'
    set -l title $argv[1]
    set -l command_name $argv[2]

    __grd_rdp_status_heading "$title"
    echo "  result: unavailable"
    printf "  reason: %s not found\n" "$command_name"
end

function __grd_rdp_status_command --description 'internal: print a formatted status command block'
    set -l title $argv[1]
    set -l seconds $argv[2]
    set -l label $argv[3]
    set -e argv[1 2 3]

    __grd_rdp_status_heading "$title"
    printf "  command: %s\n" "$label"

    set -l output (__grd_rdp_timeout "$seconds" $argv)
    set -l command_status $status
    if test $command_status -ne 0
        printf "  result: failed with status %s\n" "$command_status"
        __grd_rdp_report_status "$label" $command_status
    else
        echo "  result: ok"
    end

    __grd_rdp_print_indented $output

    return $command_status
end

function __grd_rdp_port_status --description 'internal: show listeners on TCP port 3389'
    if not command -q ss
        echo "  result: unavailable"
        echo "  reason: ss not found; install iproute2 to inspect TCP 3389."
        return 1
    end

    set -l listeners (__grd_rdp_timeout 5s ss -ltnp 2>/dev/null)
    set -l matches (string match -r '.*:3389\b.*' -- $listeners)
    if set -q matches[1]
        echo "  result: listening"
        echo "  details:"
        __grd_rdp_print_indented $matches
        return 0
    end

    if command -q sudo
        set -l sudo_listeners (__grd_rdp_timeout 5s sudo -n ss -ltnp 2>/dev/null)
        set matches (string match -r '.*:3389\b.*' -- $sudo_listeners)
        if set -q matches[1]
            echo "  result: listening"
            echo "  details:"
            __grd_rdp_print_indented $matches
            return 0
        end
    end

    echo "  result: not listening"
end

function __grd_rdp_gvariant_string --description 'internal: quote a UTF-8 string for simple GVariant text'
    set -l value $argv[1]
    if string match -q -r '[\r\n]' -- "$value"
        echo "RDP credentials cannot contain newlines." >&2
        return 1
    end

    set value (string replace -a "\\" "\\\\" -- "$value")
    set value (string replace -a "'" "\\'" -- "$value")
    printf "'%s'" "$value"
end

function __grd_rdp_report_status --description 'internal: print a concise command failure'
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
