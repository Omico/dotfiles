#!/usr/bin/env fish

set -l repo_root (path resolve (path dirname (status filename))/../..)
source "$repo_root/home/dot_config/fish/exact_conf.d/99-apm.fish"
set -g apm_test_root (mktemp -d)
set -g __apm_home "$apm_test_root/runtime"

function cleanup --on-event fish_exit
    command rm -rf "$apm_test_root"
end

function chezmoi
    echo "$apm_test_root"
end

function check --argument-names message
    if not $argv[2..-1]
        echo "FAIL: $message" >&2
        exit 1
    end
end

mkdir -p "$apm_test_root/dot_apm"
mkdir -p "$apm_test_root/bin"
printf '%s\n' '#!/bin/sh' 'echo called >> "$apm_test_root/gh-calls"' 'printf "%s\n" "$apm_test_login"' 'exit "$apm_test_status"' >"$apm_test_root/bin/gh"
chmod +x "$apm_test_root/bin/gh"
set -gx apm_test_root "$apm_test_root"
set -gx apm_test_login ''
set -gx apm_test_status 1
set -gx PATH "$apm_test_root/bin" $PATH
set -l sources "$apm_test_root/dot_apm"
printf 'dependencies:\n  apm: [shared/package]\n' >"$sources/apm.base.yml"
printf 'dependencies:\n  apm: [external/package]\n' >"$sources/apm.external.yml"
printf 'dependencies:\n  apm: [internal/package]\n' >"$sources/apm.internal.yml"
printf 'dependencies:\n  apm: [local/custom]\n' >"$sources/apm.custom.yml"
if __apm-merge-source-config </dev/null
    echo 'FAIL: missing selection accepted without terminal input' >&2
    exit 1
end
check 'missing selection not saved' test ! -e "$sources/apm.environment"
check 'missing selection leaves runtime absent' test ! -e "$__apm_home/apm.yml"
set -gx apm_test_status 0
for login in Omico omico SomeoneElse
    set -gx apm_test_login "$login"
    check 'account detection without terminal input' __apm-merge-source-config
    set -l expected external
    string match -qi Omico -- "$login"; and set expected internal
    check 'account selection saved' test (string trim <"$sources/apm.environment") = "$expected"
    rm "$sources/apm.environment"
end
set -gx apm_test_login null
set -gx apm_test_status 1
if __apm-merge-source-config </dev/null
    echo 'FAIL: failed account query accepted' >&2
    exit 1
end
check 'failed query not saved' test ! -e "$sources/apm.environment"
rm "$apm_test_root/gh-calls"
printf 'external\n' >"$sources/apm.environment"
check 'external merge' __apm-merge-source-config
check 'external package selected' test (yq '.dependencies.apm | join(",")' "$__apm_home/apm.yml") = external/package,local/custom,shared/package
check 'existing custom source selected' test (__apm-require-source-paths)[2] = "$sources/apm.custom.yml"

printf 'internal\n' >"$sources/apm.environment"
check 'internal merge' __apm-merge-source-config
check 'custom retained in internal environment' test (yq '.dependencies.apm | join(",")' "$__apm_home/apm.yml") = internal/package,local/custom,shared/package
cp "$__apm_home/apm.yml" "$apm_test_root/expected.yml"
check 'repeat merge' __apm-merge-source-config
check 'repeat stable' cmp -s "$__apm_home/apm.yml" "$apm_test_root/expected.yml"

printf 'invalid\n' >"$sources/apm.environment"
if __apm-merge-source-config 2>/dev/null
    echo 'FAIL: invalid environment accepted' >&2
    exit 1
end
check 'invalid selector preserves runtime' cmp -s "$__apm_home/apm.yml" "$apm_test_root/expected.yml"
printf 'external\n' >"$sources/apm.environment"
check 'switch back to external' __apm-merge-source-config
check 'custom retained after switch' test (yq '.dependencies.apm | join(",")' "$__apm_home/apm.yml") = external/package,local/custom,shared/package
check 'custom source unchanged' test (yq '.dependencies.apm | join(",")' "$sources/apm.custom.yml") = local/custom
check 'saved choices skip GitHub queries' test ! -e "$apm_test_root/gh-calls"
echo 'PASS: environment selection, custom preservation, repeat merge, invalid selector'
python3 "$repo_root/tests/apm/test_interaction.py"; or exit $status
