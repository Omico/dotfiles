# Homebrew

**Platforms:** macOS (`darwin`)

Manage the chezmoi-tracked `Brewfile` and keep installed packages up to date.

## `brew-backup`

Dump taps, formulae, casks, and Mac App Store apps to the repo `Brewfile`, then commit when the file changes.

## `brew-restore`

Install packages from the chezmoi `Brewfile`.

## `brew-update`

Run `brew update`, `brew upgrade`, `brew cleanup`, and `brew autoremove`, plus `mas upgrade` when `mas` is available.

## `brew-bump-omico`

Run `brew bump --tap omico/tap --no-fork --open-pr`.
