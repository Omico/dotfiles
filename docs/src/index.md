# Omico's dotfiles

This repository contains my personal dotfiles and automation setup, managed with [chezmoi](https://chezmoi.io).

## Installation

Supported platforms: macOS on Apple Silicon (native `arm64` shell) and Ubuntu 24.04.

The installer bootstraps Git, Fish, and chezmoi, then runs `chezmoi apply`. Platform-specific setup scripts install the remaining packages and configure the system. Dependencies run before file application; environment activation, application setup, and routine updates follow it. Failed setup scripts retry on the next apply. Platform package lists in `home/.chezmoidata/darwin.toml` and `home/.chezmoidata/ubuntu.toml` trigger their `run_onchange_*` installers when the rendered list changes; other one-time setup retains its existing execution rules. The full Homebrew environment remains in `Brewfile`.

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

### Rime configuration

Chezmoi writes the custom YAML files directly to `~/Library/Rime/` on macOS and `~/.local/share/fcitx5/rime/` on Linux, matching the Fcitx5 package installed on Ubuntu. The macOS-only `squirrel.custom.yaml` is excluded from Linux. Edit the shared sources under `rime/`, then run `chezmoi apply`. The user directories retain upstream dictionaries, generated files, and local data; they are not exact directories.

Install or update the upstream Rime Ice configuration separately. If using Rime auto deploy, obtain its checkout manually and run its installer, then apply the custom configuration again because the installer replaces the Rime directory and copies its own defaults:

```shell
git clone --depth=1 --branch latest https://github.com/Mark24Code/rime-auto-deploy.git "$HOME/Git/Mark24Code/rime-auto-deploy"
cd "$HOME/Git/Mark24Code/rime-auto-deploy"
./installer.rb
chezmoi apply
```

Skip cloning if the checkout already exists. On Linux, select Fcitx5 in the installer. Reload or deploy the input method after applying the custom files. Chezmoi does not manage the installer checkout or run upstream Git updates during apply.

## Upgrade local dotfiles

See [Chezmoi script naming and priority](./chezmoi-scripts.md) for lifecycle script conventions.

```shell
chezmoi update
```
