#!/usr/bin/env fish

function __mlflow_launchd_needs_subcommand
    not __fish_seen_subcommand_from install start stop restart status logs open uninstall plist help -h --help
end

complete -c mlflow-launchd -f -n __mlflow_launchd_needs_subcommand -a install -d 'Install MLflow if needed and start the LaunchAgent'
complete -c mlflow-launchd -f -n __mlflow_launchd_needs_subcommand -a start -d 'Load and start the LaunchAgent'
complete -c mlflow-launchd -f -n __mlflow_launchd_needs_subcommand -a stop -d 'Unload the LaunchAgent'
complete -c mlflow-launchd -f -n __mlflow_launchd_needs_subcommand -a restart -d 'Stop and start the LaunchAgent'
complete -c mlflow-launchd -f -n __mlflow_launchd_needs_subcommand -a status -d 'Show LaunchAgent status'
complete -c mlflow-launchd -f -n __mlflow_launchd_needs_subcommand -a logs -d 'Follow LaunchAgent stdout and stderr logs'
complete -c mlflow-launchd -f -n __mlflow_launchd_needs_subcommand -a open -d 'Open the MLflow UI in the default browser'
complete -c mlflow-launchd -f -n __mlflow_launchd_needs_subcommand -a uninstall -d 'Unload and remove the LaunchAgent plist'
complete -c mlflow-launchd -f -n __mlflow_launchd_needs_subcommand -a plist -d 'Print the installed plist, or preview when missing'
complete -c mlflow-launchd -f -n __mlflow_launchd_needs_subcommand -a help -d 'Show usage'
complete -c mlflow-launchd -f -n __mlflow_launchd_needs_subcommand -s h -d 'Show usage'
complete -c mlflow-launchd -f -n __mlflow_launchd_needs_subcommand -l help -d 'Show usage'
