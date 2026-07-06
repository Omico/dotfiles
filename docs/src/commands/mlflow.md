# MLflow

**Platforms:** macOS (`darwin`)

## `mlflow-launchd`

Manage a per-user LaunchAgent for a local MLflow tracking server. Defaults bind to `127.0.0.1:5000`.

```shell
chezmoi apply
# Open a new Fish shell after applying.
mlflow-launchd install
mlflow-launchd status
mlflow-launchd logs
mlflow-launchd open
```

### Subcommands

- **`install`** — install MLflow with `uv` when needed, write or refresh the plist, and start the service
- **`start`** — load the service; refresh the plist when settings or the MLflow binary change
- **`stop`** — unload the service
- **`restart`** — stop and start the service
- **`status`** — show plist path, URL, data and log directories, and launchd state
- **`logs`** — follow stdout and stderr log files
- **`open`** — open the MLflow UI in the default browser
- **`uninstall`** — remove the LaunchAgent plist without deleting data or logs
- **`plist`** — print the installed plist XML, or preview it when not yet installed

### Environment variables

- **`MLFLOW_HOST`** — listen address (default `127.0.0.1`)
- **`MLFLOW_PORT`** — listen port (default `5000`)
- **`MLFLOW_DATA_DIR`** — artifact and SQLite store (default `$HOME/.local/share/mlflow`)
- **`MLFLOW_STATE_DIR`** — launchd log directory (default `$HOME/.local/state/mlflow`)
