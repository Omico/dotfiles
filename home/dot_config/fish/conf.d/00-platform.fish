#!/usr/bin/env fish

function __require_linux --description 'internal: ensure current Fish platform is Linux'
    if not set -q fish_platform
        echo "fish_platform is not initialized; source the Fish config before running this command." >&2
        return 1
    end

    if test "$fish_platform" != linux
        printf "This command requires fish_platform=linux; current fish_platform is '%s'.\n" "$fish_platform" >&2
        return 1
    end
end

function __ensure_user_dbus_env --description 'internal: ensure Linux user DBus environment'
    __require_linux; or return 1

    if not command -q id
        echo "id: command not found." >&2
        return 127
    end

    set -l uid (id -u)
    set -l id_status $status
    if test $id_status -ne 0
        printf "id -u exited with status %s.\n" "$id_status" >&2
        return $id_status
    end
    if test -z "$uid"
        echo "id -u returned an empty user id." >&2
        return 1
    end

    set -l runtime_dir "/run/user/$uid"
    if not test -d "$runtime_dir"
        printf "XDG runtime directory '%s' is missing.\n" "$runtime_dir" >&2
        echo "Log in to the graphical user session first, or enable a user session for this account." >&2
        return 1
    end

    set -l bus_socket "$runtime_dir/bus"
    if not test -S "$bus_socket"
        printf "User DBus socket '%s' is missing.\n" "$bus_socket" >&2
        echo "This command needs the user DBus session from the logged-in desktop user." >&2
        return 1
    end

    set -gx XDG_RUNTIME_DIR "$runtime_dir"
    set -gx DBUS_SESSION_BUS_ADDRESS "unix:path=$bus_socket"
end
