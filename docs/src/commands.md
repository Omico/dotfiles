# Commands

## Local MLflow LaunchAgent

The `mlflow-launchd` command manages a per-user macOS LaunchAgent for a local MLflow server. Defaults bind to `127.0.0.1:5000`.

```shell
chezmoi apply
# Open a new Fish shell after applying.
mlflow-launchd install
mlflow-launchd status
mlflow-launchd logs
mlflow-launchd open
```

Subcommands:

- `install` — install MLflow via `uv` when needed, write the LaunchAgent plist when required, and start the service
- `start` — load and start the service; refresh the plist when settings or the MLflow binary change
- `stop` — unload the service
- `restart` — stop and start the service
- `status` — show plist path, URL, data/log directories, and launchd state
- `logs` — follow stdout and stderr log files
- `open` — open the MLflow UI in the default browser
- `uninstall` — unload and remove the LaunchAgent plist without deleting MLflow data or logs
- `plist` — print the installed LaunchAgent plist XML, or preview the plist when it is not installed yet

Environment overrides:

- `MLFLOW_HOST` — default `127.0.0.1`
- `MLFLOW_PORT` — default `5000`
- `MLFLOW_DATA_DIR` — default `$HOME/.local/share/mlflow`
- `MLFLOW_STATE_DIR` — default `$HOME/.local/state/mlflow`
