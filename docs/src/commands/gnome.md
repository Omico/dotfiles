# GNOME

**Platforms:** Linux (`linux`)

Helpers for the GNOME login keyring and GNOME Remote Desktop (RDP) on Ubuntu-style desktops.

## Keyring

### `gnome-keyring-status`

Report whether the login keyring is locked.

```shell
gnome-keyring-status [--quiet]
```

### `gnome-keyring-restart`

Restart the per-user Secret Service. Removes a stale `default.keyring` when it is known to block unlock.

### `gnome-keyring-unlock`

Unlock the login keyring for the current session. Requires an interactive shell for the password prompt.

## Remote Desktop

### `grd-rdp-status`

Show RDP status: `grdctl status`, the user service, and listeners on TCP port 3389.

### `grd-rdp-set-credentials`

Store RDP credentials in the Secret Service, enable RDP with `grdctl`, disable view-only mode, and restart the service. Requires an unlocked keyring and an interactive shell.

```shell
grd-rdp-set-credentials [username]
```

### `grd-rdp-restart`

Restart the `gnome-remote-desktop.service` user unit.

### `grd-rdp-fix`

Run the usual repair path: clear stuck `secret-tool`/`grdctl` processes, unlock the keyring, set credentials, and restart the service.

```shell
grd-rdp-fix [username]
```
