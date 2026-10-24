# Omico's dotfiles

This repository contains my personal dotfiles and automation setup, managed with [chezmoi](https://chezmoi.io).

## Installation

Supported platforms:

- macOS (Apple Silicon)
- Ubuntu 24.04

::: code-group

```shell [macOS (Apple Silicon)]
# Run the installation script
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Omico/dotfiles/main/install)"

# Grant Full Disk Access for Terminal via System Settings
# Open the Full Disk Access pane (or go to System Settings > Privacy & Security > Full Disk Access):
open "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles"
# Add your terminal to the list:
#   Terminal — Applications > Utilities > Terminal
#   Ghostty — Applications > Ghostty

# Install Homebrew packages
brew-restore
```

```shell [Ubuntu 24.04]
# Run the installation script
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Omico/dotfiles/main/install)"
```

:::

## Upgrade local dotfiles

```shell
chezmoi update
```
