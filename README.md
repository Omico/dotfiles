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

#### 3. Configure macOS settings

```shell
/bin/bash -c "$HOME/.local/share/chezmoi/macos"
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
