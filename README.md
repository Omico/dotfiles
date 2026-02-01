# dotfiles

## Installation

### macOS

#### 1. Run the installation script

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Omico/dotfiles/main/install)"
```

#### 2. Grant Full Disk Access for Terminal and iTerm2 via System Settings

Open the Full Disk Access pane (or go to `System Settings > Privacy & Security > Full Disk Access`):

```shell
open "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles"
```

Add both to the list:

- **Terminal** — `Applications > Utilities > Terminal`
- **iTerm2** — `Applications > iTerm.app`

#### 3. Configure macOS settings

```shell
/bin/bash -c "$HOME/.local/share/chezmoi/macos"
```

#### 4. Install Homebrew packages

```shell
brew-restore
```

#### 5. Run Rime auto deploy

```shell
cd "$HOME/Git/Mark24Code/rime-auto-deploy"
./installer.rb
```

## Upgrade local dotfiles

```shell
dotfiles-upgrade
```
