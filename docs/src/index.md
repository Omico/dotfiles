# Omico's dotfiles

This repository contains my personal dotfiles and automation setup, managed with [chezmoi](https://chezmoi.io).

## Installation

The installer bootstraps Git, Fish, and chezmoi, then runs `chezmoi apply`. Platform-specific `run_once_*` scripts install the remaining packages and configure the system. Dependencies run before file application; environment activation, application setup, and routine updates follow it. Failed setup scripts retry on the next apply; successful ones rerun only when their rendered content changes.

::: code-group

```shell [macOS]
# Run the installation script
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Omico/dotfiles/main/install)"

# Grant Full Disk Access for Terminal via System Settings
# Open the Full Disk Access pane (or go to System Settings > Privacy & Security > Full Disk Access):
open "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles"
# Add your terminal to the list:
#   Terminal — Applications > Utilities > Terminal
#   Ghostty — Applications > Ghostty

# Configure macOS settings
/bin/bash -c "$HOME/.local/share/chezmoi/macos"

# Install Homebrew packages
brew-restore
```

```shell [Ubuntu 24.04]
# Run the installation script
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Omico/dotfiles/main/install)"
```

:::

### Run Rime auto deploy

```shell
cd "$HOME/Git/Mark24Code/rime-auto-deploy"
./installer.rb
```

## Upgrade local dotfiles

See [Chezmoi script naming and priority](./chezmoi-scripts.md) for lifecycle script conventions.

```shell
chezmoi update
```
