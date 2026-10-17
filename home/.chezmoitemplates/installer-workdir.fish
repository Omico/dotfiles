set -l work (mktemp -d); or exit $status
function __installer_cleanup --on-event fish_exit --inherit-variable work
    command rm -rf -- "$work"
end
