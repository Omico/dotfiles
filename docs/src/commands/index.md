# Commands

Autoloaded Fish functions from this dotfiles repo—installed by chezmoi into `~/.config/fish/functions/`.

## Getting started

```shell
chezmoi apply
```

Open a new Fish shell, or run [`fish-reload`](./shell) in an existing session, so functions are loaded.

Source definitions live under [`home/dot_config/fish/functions/`](https://github.com/Omico/dotfiles/tree/HEAD/home/dot_config/fish/functions) in the chezmoi source tree.

## Browse by topic

| Topic | Platforms | Summary |
| --- | --- | --- |
| [APM](./apm) | All | APM CLI and agent skill packages |
| [Cloudflare WARP](./cloudflare-warp) | macOS | WARP install and Tailscale split tunneling |
| [Git](./git) | Mixed | Clone, init, reset, GitKraken, iCloud sync |
| [GNOME](./gnome) | Linux | Login keyring and Remote Desktop |
| [Homebrew](./homebrew) | macOS | Brewfile backup, restore, upgrades |
| [MLflow](./mlflow) | macOS | Local tracking server via launchd |
| [Shell](./shell) | Mixed | Reload Fish and sync configs to chezmoi |
| [Toolchains](./toolchains) | Mixed | Node.js, Bun, Rust, Flutter, Java, Gradle |
| [Xcode](./xcode) | macOS | Switch Xcode versions and open downloads |

Platform-specific functions load only when `fish_platform` matches (set at `chezmoi apply` time). Each command page lists its supported platforms.
