# dotfiles

## Installation

### macOS

#### 1. Grant Full Disk Access for Terminal via System Settings

Go to `System Settings > Privacy & Security > Full Disk Access` and add `Terminal` to the list.

By default, `Terminal` is located at `Applications > Utilities > Terminal`.

#### 2. Run the installation script

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Omico/dotfiles/main/install)"
```

#### 3. Configure Terminal

```shell
open "$HOME/.local/share/chezmoi/My.terminal"
defaults write com.apple.terminal "Default Window Settings" -string "My"
defaults write com.apple.terminal "Startup Window Settings" -string "My"
killall Terminal
```

#### 4. Install Homebrew packages

```shell
brewup restore
```

#### 5. Run Rime auto deploy

```shell
cd "$HOME/Git/Mark24Code/rime-auto-deploy"
./installer.rb
```
