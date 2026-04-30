#!/usr/bin/env fish

set -g _test_root (path resolve (status dirname)/../..)
set -g _orchard_script "$_test_root/home/dot_local/bin/executable_orchard"
set -g _failures 0
set -g _last_status 0
set -g _last_stdout ""
set -g _last_stderr ""

function _fail -a message
    set _failures (math $_failures + 1)
    printf 'not ok - %s\n' "$message" >&2
end

function _pass -a message
    printf 'ok - %s\n' "$message"
end

function _assert_status -a expected message
    if test "$_last_status" = "$expected"
        _pass "$message"
    else
        _fail "$message (expected status $expected, got $_last_status)"
        printf 'stdout:\n%s\nstderr:\n%s\n' "$_last_stdout" "$_last_stderr" >&2
    end
end

function _assert_stdout_contains -a needle message
    if string match -q "*$needle*" -- "$_last_stdout"
        _pass "$message"
    else
        _fail "$message (stdout did not contain '$needle')"
        printf 'stdout:\n%s\n' "$_last_stdout" >&2
    end
end

function _assert_stderr_contains -a needle message
    if string match -q "*$needle*" -- "$_last_stderr"
        _pass "$message"
    else
        _fail "$message (stderr did not contain '$needle')"
        printf 'stderr:\n%s\n' "$_last_stderr" >&2
    end
end

function _make_env
    set -l env_dir (mktemp -d -t orchard-validate-tests.XXXXXX)
    mkdir -p "$env_dir/config/orchard/apps" "$env_dir/cache"
    echo "$env_dir"
end

function _write_app -a env_dir name body
    printf '%s\n' "$body" >"$env_dir/config/orchard/apps/$name.fish"
end

function _run_orchard -a env_dir
    set -l stdout (mktemp -t orchard-validate-stdout.XXXXXX)
    set -l stderr (mktemp -t orchard-validate-stderr.XXXXXX)

    env XDG_CONFIG_HOME="$env_dir/config" XDG_CACHE_HOME="$env_dir/cache" fish "$_orchard_script" $argv[2..-1] >"$stdout" 2>"$stderr"
    set _last_status $status
    set _last_stdout (cat "$stdout")
    set _last_stderr (cat "$stderr")

    rm -f "$stdout" "$stderr"
end

function _test_valid_packages_pass
    set -l env_dir (_make_env)

    _write_app "$env_dir" valid-static 'set -g orchard_app_id valid-static
set -g orchard_app_display_name "Valid Static"
set -g orchard_app_download_url "https://example.com/ValidStatic.dmg"
set -g orchard_app_download_type dmg'

    _write_app "$env_dir" valid-dynamic 'set -g orchard_app_id valid-dynamic
set -g orchard_app_display_name "Valid Dynamic"
set -g orchard_app_download_type zip

function orchard_resolve_download_url_callback
    set -g orchard_app_download_url "https://example.com/ValidDynamic.zip"
    return 0
end'

    _run_orchard "$env_dir" validate
    _assert_status 0 "validate accepts static and dynamic packages"
    _assert_stdout_contains "✓ valid-static" "validate marks successful static package"
    _assert_stdout_contains "✓ valid-dynamic" "validate marks successful dynamic package"
    _assert_stdout_contains "✓ Validated 2 orchard app package(s)." "validate reports validated count with success marker"

    rm -rf "$env_dir"
end

function _test_id_mismatch_fails
    set -l env_dir (_make_env)

    _write_app "$env_dir" wrong-name 'set -g orchard_app_id other-name
set -g orchard_app_display_name "Wrong Name"
set -g orchard_app_download_url "https://example.com/WrongName.dmg"
set -g orchard_app_download_type dmg'

    _run_orchard "$env_dir" validate
    _assert_status 1 "validate rejects app_id that differs from filename"
    _assert_stderr_contains "✗ wrong-name" "validate marks failed package"
    _assert_stderr_contains "wrong-name: orchard_app_id must match filename" "validate explains app_id mismatch"

    rm -rf "$env_dir"
end

function _test_missing_url_without_callback_fails
    set -l env_dir (_make_env)

    _write_app "$env_dir" missing-url 'set -g orchard_app_id missing-url
set -g orchard_app_display_name "Missing URL"
set -g orchard_app_download_type dmg'

    _run_orchard "$env_dir" validate missing-url
    _assert_status 1 "validate rejects missing download URL without resolver"
    _assert_stderr_contains "missing-url: orchard_app_download_url is required unless orchard_resolve_download_url_callback is defined" "validate explains missing download URL"

    rm -rf "$env_dir"
end

function _test_callbacks_do_not_leak_between_packages
    set -l env_dir (_make_env)

    _write_app "$env_dir" callback-first 'set -g orchard_app_id callback-first
set -g orchard_app_display_name "Callback First"
set -g orchard_app_download_type dmg

function orchard_resolve_download_url_callback
    set -g orchard_app_download_url "https://example.com/CallbackFirst.dmg"
    return 0
end'

    _write_app "$env_dir" missing-url 'set -g orchard_app_id missing-url
set -g orchard_app_display_name "Missing URL"
set -g orchard_app_download_type dmg'

    _run_orchard "$env_dir" validate
    _assert_status 1 "validate clears callbacks between packages"
    _assert_stderr_contains "missing-url: orchard_app_download_url is required unless orchard_resolve_download_url_callback is defined" "validate catches missing URL after callback package"

    rm -rf "$env_dir"
end

_test_valid_packages_pass
_test_id_mismatch_fails
_test_missing_url_without_callback_fails
_test_callbacks_do_not_leak_between_packages

if test $_failures -gt 0
    printf '%s test assertion(s) failed.\n' "$_failures" >&2
    exit 1
end

printf 'All orchard validate tests passed.\n'
