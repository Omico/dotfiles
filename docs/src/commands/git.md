# Git

Repository workflows, Git clients, and macOS-specific sync helpers.

## `gcl`

**Platforms:** All

Clone a repository into a directory layout derived from its remote URL. Unconfigured hosts use `$HOME/Git/<remote-path>`.

SCP-style remotes accept an optional username: both `git@host:team/repo.git` and `host:team/repo.git` preserve `team/repo` and use the same host-specific clone root.

```shell
gcl <repository> [git-clone-args...]
```

Override clone roots per host with `gcl_remote_host_base_dirs` (host/base-dir pairs):

```fish
set -g gcl_remote_host_base_dirs \
    gitlab.com "$HOME/GitLab" \
    git.company.com "$HOME/Work/GitLab"
```

## `gi`

**Platforms:** All

Initialize a repository in the current directory: `git init`, stage all files, create an initial commit, and rename `master` to `main` when needed. Prompts before deleting an existing `.git` directory.

Stop at the first failed removal, initialization, staging, commit, or branch operation and return its error status. Earlier successful steps are retained.

## `gitkraken`

**Platforms:** macOS (`darwin`)

Open GitKraken, optionally with a project directory.

Project paths are passed literally; quote paths containing spaces or shell metacharacters.

```shell
gitkraken [project_path]
```

- **`GITKRAKEN_APP_PATH`** — app bundle path (default `/Applications/GitKraken.app`)

## `stop-sync-gitignored`

**Platforms:** macOS (`darwin`)

Mark gitignored paths with the `com.apple.fileprovider.ignore#P` extended attribute so iCloud File Provider stops syncing them.

Ignored filenames retain embedded newlines. If Git cannot list ignored paths, return its error status without marking anything; `--dry-run` follows the same failure rule.

```shell
stop-sync-gitignored [--dry-run] [path]
```

## `update-git-repo`

**Platforms:** macOS (`darwin`)

Fetch all remotes and hard-reset a local clone to `origin/HEAD`.

```shell
update-git-repo <repo_dir>
```
