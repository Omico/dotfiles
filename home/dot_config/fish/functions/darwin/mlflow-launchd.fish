#!/usr/bin/env fish

# Environment overrides:
#   MLFLOW_HOST       Default: 127.0.0.1
#   MLFLOW_PORT       Default: 5000
#   MLFLOW_DATA_DIR   Default: $HOME/.local/share/mlflow
#   MLFLOW_STATE_DIR  Default: $HOME/.local/state/mlflow
function mlflow-launchd --description "Manage a per-user macOS LaunchAgent for local MLflow"
    __mlflow_launchd_require_macos; or return 1
    __mlflow_launchd_set_context; or return 1

    set -l subcommand help
    set -q argv[1]; and set subcommand $argv[1]
    set -l command_status 0

    switch "$subcommand"
        case install
            __mlflow_launchd_install_service
            set command_status $status
        case start
            __mlflow_launchd_start_service
            set command_status $status
        case stop
            __mlflow_launchd_stop_service
            set command_status $status
        case restart
            __mlflow_launchd_restart_service
            set command_status $status
        case status
            __mlflow_launchd_status_service
            set command_status $status
        case logs
            __mlflow_launchd_logs_service
            set command_status $status
        case open
            __mlflow_launchd_open_service
            set command_status $status
        case uninstall
            __mlflow_launchd_uninstall_service
            set command_status $status
        case plist
            __mlflow_launchd_print_plist
            set command_status $status
        case help -h --help
            __mlflow_launchd_usage
            set command_status $status
        case '*'
            printf "Unknown command: %s\n\n" "$subcommand" >&2
            __mlflow_launchd_usage >&2
            set command_status 2
    end

    __mlflow_launchd_clear_context
    return $command_status
end

function __mlflow_launchd_usage
    echo "Usage:"
    echo "  mlflow-launchd install"
    echo "  mlflow-launchd start"
    echo "  mlflow-launchd stop"
    echo "  mlflow-launchd restart"
    echo "  mlflow-launchd status"
    echo "  mlflow-launchd logs"
    echo "  mlflow-launchd open"
    echo "  mlflow-launchd uninstall"
    echo "  mlflow-launchd plist     Print the installed plist, or preview when missing"
    echo "  mlflow-launchd help"
    echo
    echo "Environment overrides:"
    echo "  MLFLOW_HOST       Default: 127.0.0.1"
    echo "  MLFLOW_PORT       Default: 5000"
    echo "  MLFLOW_DATA_DIR   Default: \$HOME/.local/share/mlflow"
    echo "  MLFLOW_STATE_DIR  Default: \$HOME/.local/state/mlflow"
end

function __mlflow_launchd_require_macos
    if not set -q fish_platform
        echo "fish_platform is not initialized; source the Fish config before running this command." >&2
        return 1
    end

    if test "$fish_platform" != darwin
        printf "mlflow-launchd requires fish_platform=darwin; current fish_platform is '%s'.\n" "$fish_platform" >&2
        return 1
    end
end

function __mlflow_launchd_set_context
    set -l host 127.0.0.1
    set -l port 5000
    set -l data_dir "$HOME/.local/share/mlflow"
    set -l state_dir "$HOME/.local/state/mlflow"

    set -q MLFLOW_HOST; and set host "$MLFLOW_HOST"
    set -q MLFLOW_PORT; and set port "$MLFLOW_PORT"
    set -q MLFLOW_DATA_DIR; and set data_dir "$MLFLOW_DATA_DIR"
    set -q MLFLOW_STATE_DIR; and set state_dir "$MLFLOW_STATE_DIR"

    if not string match -qr '^[0-9]+$' -- "$port"
        printf "MLFLOW_PORT must be a numeric port; got '%s'.\n" "$port" >&2
        return 1
    end

    if test "$port" -lt 1 -o "$port" -gt 65535
        printf "MLFLOW_PORT must be between 1 and 65535; got '%s'.\n" "$port" >&2
        return 1
    end

    set -g __mlflow_launchd_label io.local.mlflow
    set -g __mlflow_launchd_plist "$HOME/Library/LaunchAgents/$__mlflow_launchd_label.plist"
    set -g __mlflow_launchd_domain "gui/"(command id -u)
    set -g __mlflow_launchd_service "$__mlflow_launchd_domain/$__mlflow_launchd_label"
    set -g __mlflow_launchd_host "$host"
    set -g __mlflow_launchd_port "$port"
    set -g __mlflow_launchd_data_dir "$data_dir"
    set -g __mlflow_launchd_state_dir "$state_dir"

    set -g __mlflow_launchd_db_path "$__mlflow_launchd_data_dir/mlflow.db"
    set -g __mlflow_launchd_artifact_dir "$__mlflow_launchd_data_dir/artifacts"
    set -g __mlflow_launchd_out_log "$__mlflow_launchd_state_dir/mlflow.out.log"
    set -g __mlflow_launchd_err_log "$__mlflow_launchd_state_dir/mlflow.err.log"
    set -g __mlflow_launchd_backend_store_uri "sqlite:///$__mlflow_launchd_db_path"
    set -g __mlflow_launchd_artifact_root "file://$__mlflow_launchd_artifact_dir"
    set -g __mlflow_launchd_url (printf "http://%s:%s" "$__mlflow_launchd_host" "$__mlflow_launchd_port")

    return 0
end

function __mlflow_launchd_clear_context
    set -e __mlflow_launchd_label
    set -e __mlflow_launchd_plist
    set -e __mlflow_launchd_domain
    set -e __mlflow_launchd_service
    set -e __mlflow_launchd_host
    set -e __mlflow_launchd_port
    set -e __mlflow_launchd_data_dir
    set -e __mlflow_launchd_state_dir
    set -e __mlflow_launchd_db_path
    set -e __mlflow_launchd_artifact_dir
    set -e __mlflow_launchd_out_log
    set -e __mlflow_launchd_err_log
    set -e __mlflow_launchd_backend_store_uri
    set -e __mlflow_launchd_artifact_root
    set -e __mlflow_launchd_url
end

function __mlflow_launchd_xml_escape
    set -l value "$argv[1]"
    set value (string replace -a "&" "&amp;" -- "$value")
    set value (string replace -a "<" "&lt;" -- "$value")
    set value (string replace -a ">" "&gt;" -- "$value")
    set value (string replace -a '"' "&quot;" -- "$value")
    set value (string replace -a "'" "&apos;" -- "$value")
    printf "%s" "$value"
end

function __mlflow_launchd_absolute_executable_path
    set -l candidate "$argv[1]"

    if test -z "$candidate"; or not test -x "$candidate"; or test -d "$candidate"
        return 1
    end

    if string match -q "/*" -- "$candidate"
        printf "%s\n" "$candidate"
        return 0
    end

    set -l candidate_dir (command dirname "$candidate")
    set -l candidate_base (command basename "$candidate")
    set -l absolute_dir (cd "$candidate_dir"; and command pwd -P)
    or return 1

    printf "%s/%s\n" "$absolute_dir" "$candidate_base"
end

function __mlflow_launchd_find_mlflow_binary
    for candidate in (command -s mlflow 2>/dev/null)
        __mlflow_launchd_absolute_executable_path "$candidate"; and return 0
    end

    for candidate in "$HOME/.local/bin/mlflow" "$HOME/.cargo/bin/mlflow"
        __mlflow_launchd_absolute_executable_path "$candidate"; and return 0
    end

    if command -q uv
        set -l uv_bin_dir (command uv tool dir --bin 2>/dev/null)
        if test -n "$uv_bin_dir"
            __mlflow_launchd_absolute_executable_path "$uv_bin_dir/mlflow"; and return 0
        end
    end

    return 1
end

function __mlflow_launchd_resolve_mlflow_binary
    set -l allow_install false
    if set -q argv[1]; and test "$argv[1]" = --install
        set allow_install true
    end

    set -l mlflow_bin (__mlflow_launchd_find_mlflow_binary)
    if test $status -eq 0
        printf "%s\n" "$mlflow_bin"
        return 0
    end

    if not $allow_install
        echo "mlflow command was not found." >&2
        echo "Install MLflow yourself, or run: mlflow-launchd install" >&2
        return 1
    end

    if not command -q uv
        echo "mlflow command was not found, and uv is not installed." >&2
        echo "Install MLflow yourself, or install uv so this command can run:" >&2
        echo "  uv tool install mlflow" >&2
        return 1
    end

    echo "mlflow command was not found; installing persistent uv tool: mlflow" >&2
    command uv tool install mlflow >&2; or return 1

    set mlflow_bin (__mlflow_launchd_find_mlflow_binary)
    if test $status -eq 0
        printf "%s\n" "$mlflow_bin"
        return 0
    end

    echo "Installed mlflow with uv, but the mlflow command could not be found." >&2
    echo "Ensure uv's tool bin directory is on PATH, then rerun this command." >&2
    return 1
end

function __mlflow_launchd_ensure_directories
    command mkdir -p (command dirname "$__mlflow_launchd_plist") "$__mlflow_launchd_data_dir" "$__mlflow_launchd_artifact_dir" "$__mlflow_launchd_state_dir"; or return 1
end

function __mlflow_launchd_program_arguments
    set -l mlflow_bin "$argv[1]"

    printf '%s\n' \
        "$mlflow_bin" \
        server \
        --host "$__mlflow_launchd_host" \
        --port "$__mlflow_launchd_port" \
        --backend-store-uri "$__mlflow_launchd_backend_store_uri" \
        --default-artifact-root "$__mlflow_launchd_artifact_root"
end

function __mlflow_launchd_render_plist
    set -l mlflow_bin "$argv[1]"
    set -l program_args (__mlflow_launchd_program_arguments "$mlflow_bin")

    echo '<?xml version="1.0" encoding="UTF-8"?>'
    echo '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">'
    echo '<plist version="1.0">'
    echo '<dict>'
    echo '    <key>Label</key>'
    printf '    <string>%s</string>\n' (__mlflow_launchd_xml_escape "$__mlflow_launchd_label")
    echo '    <key>ProgramArguments</key>'
    echo '    <array>'
    for arg in $program_args
        printf '        <string>%s</string>\n' (__mlflow_launchd_xml_escape "$arg")
    end
    echo '    </array>'
    echo '    <key>RunAtLoad</key>'
    echo '    <true/>'
    echo '    <key>KeepAlive</key>'
    echo '    <true/>'
    echo '    <key>WorkingDirectory</key>'
    printf '    <string>%s</string>\n' (__mlflow_launchd_xml_escape "$__mlflow_launchd_data_dir")
    echo '    <key>StandardOutPath</key>'
    printf '    <string>%s</string>\n' (__mlflow_launchd_xml_escape "$__mlflow_launchd_out_log")
    echo '    <key>StandardErrorPath</key>'
    printf '    <string>%s</string>\n' (__mlflow_launchd_xml_escape "$__mlflow_launchd_err_log")
    echo '</dict>'
    echo '</plist>'
end

function __mlflow_launchd_plist_needs_refresh
    if not test -f "$__mlflow_launchd_plist"
        return 0
    end

    command plutil -lint "$__mlflow_launchd_plist" >/dev/null 2>&1; or return 0

    set -l mlflow_bin_for_compare (command plutil -extract ProgramArguments.0 raw -o - "$__mlflow_launchd_plist" 2>/dev/null)
    set -l discovered_bin (__mlflow_launchd_find_mlflow_binary)
    if test $status -eq 0
        set mlflow_bin_for_compare "$discovered_bin"
    end

    set -l expected_args (__mlflow_launchd_program_arguments "$mlflow_bin_for_compare")
    set -l index 0
    for expected_arg in $expected_args
        set -l plist_arg (command plutil -extract "ProgramArguments.$index" raw -o - "$__mlflow_launchd_plist" 2>/dev/null)
        if test $status -ne 0; or test "$plist_arg" != "$expected_arg"
            return 0
        end
        set index (math $index + 1)
    end

    set -l plist_workdir (command plutil -extract WorkingDirectory raw -o - "$__mlflow_launchd_plist" 2>/dev/null)
    test "$plist_workdir" = "$__mlflow_launchd_data_dir"; or return 0

    set -l plist_stdout (command plutil -extract StandardOutPath raw -o - "$__mlflow_launchd_plist" 2>/dev/null)
    test "$plist_stdout" = "$__mlflow_launchd_out_log"; or return 0

    set -l plist_stderr (command plutil -extract StandardErrorPath raw -o - "$__mlflow_launchd_plist" 2>/dev/null)
    test "$plist_stderr" = "$__mlflow_launchd_err_log"; or return 0

    return 1
end

function __mlflow_launchd_write_plist
    set -l allow_install false
    if set -q argv[1]; and test "$argv[1]" = --install
        set allow_install true
    end

    set -l mlflow_bin
    if $allow_install
        set mlflow_bin (__mlflow_launchd_resolve_mlflow_binary --install)
    else
        set mlflow_bin (__mlflow_launchd_resolve_mlflow_binary)
    end
    if test $status -ne 0
        return 1
    end

    __mlflow_launchd_ensure_directories; or return 1
    __mlflow_launchd_render_plist "$mlflow_bin" >"$__mlflow_launchd_plist"; or return 1
    command plutil -lint "$__mlflow_launchd_plist" >/dev/null
end

function __mlflow_launchd_print_plist
    if test -f "$__mlflow_launchd_plist"
        command plutil -lint "$__mlflow_launchd_plist" >/dev/null; or return 1
        command cat "$__mlflow_launchd_plist"
        return 0
    end

    set -l mlflow_bin (__mlflow_launchd_find_mlflow_binary)
    if test $status -ne 0
        echo "mlflow command was not found; cannot render LaunchAgent plist." >&2
        echo "Install MLflow yourself, or run: mlflow-launchd install" >&2
        return 1
    end

    __mlflow_launchd_render_plist "$mlflow_bin"
end

function __mlflow_launchd_is_loaded
    command launchctl print "$__mlflow_launchd_service" >/dev/null 2>&1
end

function __mlflow_launchd_load_service
    command launchctl bootstrap "$__mlflow_launchd_domain" "$__mlflow_launchd_plist"
end

function __mlflow_launchd_unload_service
    __mlflow_launchd_is_loaded; or return 0

    if test -f "$__mlflow_launchd_plist"
        command launchctl bootout "$__mlflow_launchd_domain" "$__mlflow_launchd_plist" 2>/dev/null
        or command launchctl bootout "$__mlflow_launchd_service"
    else
        command launchctl bootout "$__mlflow_launchd_service"
    end
end

function __mlflow_launchd_kickstart_service
    command launchctl kickstart -k "$__mlflow_launchd_service"
end

function __mlflow_launchd_write_plist_and_reload
    set -l allow_install false
    if set -q argv[1]; and test "$argv[1]" = --install
        set allow_install true
    end

    if $allow_install
        __mlflow_launchd_write_plist --install; or return 1
    else
        __mlflow_launchd_write_plist; or return 1
    end

    __mlflow_launchd_unload_service; or return 1
    __mlflow_launchd_load_service; or return 1
end

function __mlflow_launchd_install_service
    if __mlflow_launchd_plist_needs_refresh
        __mlflow_launchd_write_plist_and_reload --install; or return 1
    else
        __mlflow_launchd_resolve_mlflow_binary --install; or return 1
        command plutil -lint "$__mlflow_launchd_plist" >/dev/null; or return 1
        __mlflow_launchd_ensure_directories; or return 1
        __mlflow_launchd_is_loaded; or __mlflow_launchd_load_service; or return 1
    end

    __mlflow_launchd_kickstart_service; or return 1
    printf "Installed and started %s at %s\n" "$__mlflow_launchd_label" "$__mlflow_launchd_url"
end

function __mlflow_launchd_start_service
    if __mlflow_launchd_plist_needs_refresh
        __mlflow_launchd_write_plist_and_reload; or return 1
    else
        command plutil -lint "$__mlflow_launchd_plist" >/dev/null; or return 1
        __mlflow_launchd_ensure_directories; or return 1
        __mlflow_launchd_is_loaded; or __mlflow_launchd_load_service; or return 1
    end

    __mlflow_launchd_kickstart_service; or return 1
    printf "Started %s at %s\n" "$__mlflow_launchd_label" "$__mlflow_launchd_url"
end

function __mlflow_launchd_stop_service
    __mlflow_launchd_unload_service; or return 1
    printf "Stopped %s\n" "$__mlflow_launchd_label"
end

function __mlflow_launchd_restart_service
    __mlflow_launchd_stop_service; or return 1
    __mlflow_launchd_start_service
end

function __mlflow_launchd_status_service
    printf "label: %s\n" "$__mlflow_launchd_label"
    printf "plist path: %s\n" "$__mlflow_launchd_plist"
    printf "URL: %s\n" "$__mlflow_launchd_url"
    printf "data directory: %s\n" "$__mlflow_launchd_data_dir"
    printf "log directory: %s\n" "$__mlflow_launchd_state_dir"

    set -l status_output (command launchctl print "$__mlflow_launchd_service" 2>&1)
    if test $status -eq 0
        echo "launchd status: loaded"
        for line in $status_output
            set -l trimmed (string trim -- "$line")
            if string match -q -r '^state = ' -- "$trimmed"
                printf "state: %s\n" (string replace -r '^state = ' '' -- "$trimmed")
            else if string match -q -r '^pid = ' -- "$trimmed"
                printf "pid: %s\n" (string replace -r '^pid = ' '' -- "$trimmed")
            else if string match -q -r '^last exit code = ' -- "$trimmed"
                printf "%s\n" "$trimmed"
            end
        end
    else
        echo "launchd status: not loaded"
        printf "launchd detail: %s\n" "$status_output"
    end
end

function __mlflow_launchd_logs_service
    command mkdir -p "$__mlflow_launchd_state_dir"; or return 1
    command touch "$__mlflow_launchd_out_log" "$__mlflow_launchd_err_log"; or return 1
    command tail -f "$__mlflow_launchd_out_log" "$__mlflow_launchd_err_log"
end

function __mlflow_launchd_open_service
    command open "$__mlflow_launchd_url"
end

function __mlflow_launchd_uninstall_service
    __mlflow_launchd_unload_service; or return 1
    command rm -f "$__mlflow_launchd_plist"; or return 1
    printf "Removed %s\n" "$__mlflow_launchd_plist"
    echo "MLflow data and logs were left in place:"
    printf "  %s\n" "$__mlflow_launchd_data_dir"
    printf "  %s\n" "$__mlflow_launchd_state_dir"
end
