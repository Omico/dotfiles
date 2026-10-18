#!/usr/bin/env fish

command -q fnm; or exit 0

fnm-upgrade-latest-lts; or exit $status

exit 0
