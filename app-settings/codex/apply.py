# /// script
# requires-python = ">=3.11"
# dependencies = ["tomlkit==0.13.3"]
# ///
"""Apply selected Codex preferences without owning its runtime configuration."""

import argparse
from collections.abc import Mapping
import copy
import fcntl
import math
import os
from pathlib import Path
import stat
import tempfile

import tomlkit


def identity(info):
    if info is None:
        return None
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink,
            info.st_uid, info.st_gid, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def read(path, optional=False):
    try:
        info = path.lstat()
    except FileNotFoundError:
        if optional:
            return b"", None
        raise
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise ValueError(f"Expected a regular, unlinked file: {path}")
    data = path.read_bytes()
    if identity(path.lstat()) != identity(info):
        raise ValueError(f"File changed while reading: {path}")
    return data, info


def parse(data):
    return tomlkit.parse(data.decode("utf-8"))


def equivalent(left, right):
    left = left.unwrap() if hasattr(left, "unwrap") else left
    right = right.unwrap() if hasattr(right, "unwrap") else right
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(equivalent(left[k], right[k]) for k in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(equivalent(a, b) for a, b in zip(left, right))
    if isinstance(left, float) and math.isnan(left) and math.isnan(right):
        return True
    return left == right


def leaves(table, prefix=()):
    for key, value in table.items():
        path = (*prefix, key)
        if isinstance(value, Mapping):
            yield from leaves(value, path)
        else:
            yield path, value


def paths(value):
    if not isinstance(value, list):
        raise ValueError("Field paths must be an array of string arrays")
    result = set()
    for path in value:
        if not isinstance(path, list) or not path or not all(isinstance(k, str) and k for k in path):
            raise ValueError("Each field path must be a nonempty string array")
        result.add(tuple(path))
    return result


def plan(live, shared, local):
    if set(shared) - {"settings", "remove"} or set(local) - {"preserve"}:
        raise ValueError("Unknown sync control field")
    settings = shared.get("settings", {})
    if not isinstance(settings, Mapping):
        raise ValueError("settings must be a table")
    updates = dict(leaves(settings))
    removed = paths(shared.get("remove", []))
    preserved = paths(local.get("preserve", []))
    owned = set(updates) | removed
    if set(updates) & removed:
        raise ValueError("A field cannot be set and removed together")
    for path in owned:
        if any(path[:i] in owned for i in range(1, len(path))):
            raise ValueError("Field paths cannot overlap")
    result = copy.deepcopy(live)
    changed = []
    for path in sorted(owned - preserved):
        table = result
        for key in path[:-1]:
            if key not in table:
                if path in removed:
                    break
                table[key] = tomlkit.table()
            if not isinstance(table[key], Mapping):
                raise ValueError(f"Expected a table at {path}")
            table = table[key]
        else:
            key = path[-1]
            if path in removed:
                if key in table:
                    # Deletion owns one leaf, never a whole runtime table.
                    if isinstance(table[key], Mapping):
                        raise ValueError(f"Cannot remove a table: {path}")
                    del table[key]
                    changed.append(path)
            elif key not in table or not equivalent(table[key], updates[path]):
                if key in table and isinstance(table[key], Mapping):
                    raise ValueError(f"Cannot replace a table: {path}")
                table[key] = copy.deepcopy(updates[path])
                changed.append(path)
    candidate = tomlkit.dumps(result).encode("utf-8")
    if not equivalent(parse(candidate), result):
        raise ValueError("Candidate TOML did not round-trip")
    return candidate, changed


def unchanged(path, snapshot):
    data, info = read(path, optional=True)
    if data != snapshot[0] or identity(info) != identity(snapshot[1]):
        raise ValueError(f"File changed; run apply again: {path}")


def publish(path, snapshot, candidate, inputs):
    """Back up and atomically replace a configuration after snapshot checks."""
    data, info = snapshot
    mode = stat.S_IMODE(info.st_mode) if info else 0o600
    fd, name = tempfile.mkstemp(prefix=".codex-settings-", dir=path.parent)
    staged = Path(name)
    backup = None
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(candidate)
            stream.flush()
            os.fchmod(stream.fileno(), mode)
            os.fsync(stream.fileno())
        for source, original in inputs:
            unchanged(source, original)
        unchanged(path, snapshot)
        if info:
            backup_dir = path.parent / "settings-sync-backups"
            backup_dir.mkdir(mode=0o700, exist_ok=True)
            if backup_dir.is_symlink() or stat.S_IMODE(backup_dir.stat().st_mode) != 0o700:
                raise ValueError("Backup directory must be private and not a symlink")
            backup_fd, backup_name = tempfile.mkstemp(prefix="config-", suffix=".toml", dir=backup_dir)
            backup = Path(backup_name)
            with os.fdopen(backup_fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        for source, original in inputs:
            unchanged(source, original)
        unchanged(path, snapshot)
        os.replace(staged, path)
        return backup
    finally:
        staged.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Validate and list changes without writing")
    args = parser.parse_args()
    directory = Path(__file__).resolve().parent
    shared_path = directory / "settings.shared.toml"
    local_path = Path.home() / ".config/codex-settings/settings.local.toml"
    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
    live_path = codex_home / "config.toml"
    shared = read(shared_path)
    local = read(local_path, optional=True)
    snapshot = read(live_path, optional=True)
    candidate, changed = plan(parse(snapshot[0]), parse(shared[0]), parse(local[0]))
    for field in changed:
        print("Change: " + repr(list(field)))
    if args.dry_run or not changed:
        print("Candidate valid; " + ("no changes." if not changed else "dry run only."))
        return
    codex_home.mkdir(mode=0o700, parents=True, exist_ok=True)
    lock_path = codex_home / ".settings-sync.lock"
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        backup = publish(live_path, snapshot, candidate, [(shared_path, shared), (local_path, local)])
    print(f"Applied {len(changed)} field changes. Backup: {backup or 'new file'}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, tomlkit.exceptions.ParseError) as error:
        raise SystemExit(f"Error: {error}") from error
