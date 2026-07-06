# APM

**Platforms:** All

Wrappers around the [APM](https://aka.ms/apm-unix) CLI for installing the binary and managing agent skill packages in this dotfiles repo.

## `apm`

Forwards to the APM CLI. Installs to `/usr/local/bin/apm` via the official Unix installer when the binary is missing.

## `apm-add-skill`

Adds skill packages to an APM source config, runs `apm install`, and tracks the updated source file with `chezmoi add`.

```shell
apm-add-skill [--global] <package> [<package> ...]
```

- **Default** — write packages to the local custom source
- **`--global`** — write packages to the tracked base source
- **Package refs** — `github.com/owner/repo/path/to/skill`, or GitHub blob URLs (normalized automatically)

## `apm-update`

Refreshes agent skills from `~/.apm`: merge source configs, run `apm self-update`, then `apm update --yes --parallel-downloads 32`, and relink skills into agent directories.
