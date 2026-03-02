# Orchard completions for Fish shell

function __orchard_app_ids
    set -q XDG_CONFIG_HOME; or set XDG_CONFIG_HOME $HOME/.config
    set -l apps_dir "$XDG_CONFIG_HOME/orchard/apps"
    if test -d "$apps_dir"
        for f in $apps_dir/*.fish
            string replace -r '.*/([^/]+)\.fish$' '$1' -- $f
        end
    end
end

function __orchard_subcommands
    echo list
    echo install
    echo migrate
    echo cleanup
end

function __orchard_needs_subcommand
    not __fish_seen_subcommand_from (__orchard_subcommands)
end

# First arg subcommands:
# - list
# - install
# - migrate
# - cleanup
complete -c orchard -c executable_orchard -f -n __orchard_needs_subcommand -a list -d 'List all app definitions and install status'
complete -c orchard -c executable_orchard -f -n __orchard_needs_subcommand -a install -d 'Download and install the given app'
complete -c orchard -c executable_orchard -f -n __orchard_needs_subcommand -a migrate -d 'Migrate from other sources (e.g. Homebrew casks)'
complete -c orchard -c executable_orchard -f -n __orchard_needs_subcommand -a cleanup -d 'Remove orchard cache directory'

# After install:
# - argument:
#   - <app_id>
# - options:
#   - --force
complete -c orchard -c executable_orchard -n '__fish_seen_subcommand_from install' -l force -d 'Force re-download'
complete -c orchard -c executable_orchard -n '__fish_seen_subcommand_from install' -xa '(__orchard_app_ids)'

# After migrate:
# - argument:
#   - <source> (currently brew)
complete -c orchard -c executable_orchard -n '__fish_seen_subcommand_from migrate' -a brew -d 'Migrate outdated Homebrew casks to orchard'
