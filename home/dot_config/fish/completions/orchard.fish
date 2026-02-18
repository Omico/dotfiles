# orchard / executable_orchard: subcommand and app_id completion

function __orchard_app_ids
    set -q XDG_CONFIG_HOME; or set XDG_CONFIG_HOME $HOME/.config
    set -l apps_dir "$XDG_CONFIG_HOME/orchard/apps"
    if test -d "$apps_dir"
        for f in $apps_dir/*.fish
            string replace -r '.*/([^/]+)\.fish$' '$1' -- $f
        end
    end
end

# First arg: list / install / cleanup
complete -c orchard -c executable_orchard -f -n 'not __fish_seen_subcommand_from list install cleanup' -a 'list' -d 'List all app definitions and install status'
complete -c orchard -c executable_orchard -f -n 'not __fish_seen_subcommand_from list install cleanup' -a 'install' -d 'Download and install the given app'
complete -c orchard -c executable_orchard -f -n 'not __fish_seen_subcommand_from list install cleanup' -a 'cleanup' -d 'Remove orchard cache directory'

# After install: --force or app_id
complete -c orchard -c executable_orchard -n '__fish_seen_subcommand_from install' -l force -d 'Force re-download'
complete -c orchard -c executable_orchard -n '__fish_seen_subcommand_from install' -xa '(__orchard_app_ids)'
