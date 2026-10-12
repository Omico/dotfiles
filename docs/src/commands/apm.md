# APM

**Platforms:** All

Install and update agent skills with [APM](https://aka.ms/apm-unix).

## Choose an environment

On first use, `apm-update` or `apm-add-skill` uses the GitHub account from `gh`: `Omico` selects `internal`; other accounts select `external`. If detection fails, choose manually. The selection is saved for later calls.

To set the environment manually, write `external` or `internal` to `home/dot_apm/apm.environment` in the chezmoi source directory. This selects the corresponding dependency file and keeps additions from `apm.custom.yml`. Unattended commands require a saved selection or successful account detection.

## `apm`

Run an APM command. The wrapper installs the CLI on first use if needed.

```shell
apm --help
```

## `apm-add-skill`

Add and install one or more skills:

```shell
apm-add-skill <package> [<package> ...]
apm-add-skill --global <package> [<package> ...]
```

- **Default:** save to the local `apm.custom.yml`.
- **`--global`:** save to the tracked `apm.base.yml`, shared by both environments.
- **Package:** use `owner/repo/path/to/skill` or a GitHub file URL.

For tracked additions specific to one environment, edit `home/dot_apm/apm.external.yml` or `home/dot_apm/apm.internal.yml` in the chezmoi source directory.

## `apm-update`

Update the APM CLI and all skills configured for the selected environment, including local additions:

```shell
apm-update
```
