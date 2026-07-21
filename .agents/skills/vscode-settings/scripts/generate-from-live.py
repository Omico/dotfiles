#!/usr/bin/env python3
"""Generate managed vscode-settings layers from live Code and Cursor User settings."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import sys
import tempfile
from typing import Any

from vscode_settings_jsonc import JsoncError
from vscode_settings_jsonc import load_jsonc_object as parse_jsonc_object

EXIT_USAGE = 2
EXIT_OPERATIONAL = 1


def fail(message: str, *, code: int = EXIT_USAGE) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def load_ignored_keys(path: pathlib.Path) -> set[str]:
    if path.is_symlink():
        fail(f"Error: ignored input is not a regular file: {path}")
    if not path.is_file():
        if path.exists():
            fail(f"Error: ignored input is not a regular file: {path}")
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f"Error: invalid JSON in {path}: {exc}")
    if not isinstance(data, list) or not all(isinstance(item, str) for item in data):
        fail(f"Error: ignored file must be a JSON array of strings: {path}")
    return set(data)


def serialize_json(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n"


def write_json_layers(layers: list[tuple[pathlib.Path, Any]]) -> None:
    prepared: list[tuple[pathlib.Path, pathlib.Path, pathlib.Path | None]] = []
    replaced: list[tuple[pathlib.Path, pathlib.Path | None]] = []
    preserved_backups: set[pathlib.Path] = set()

    try:
        for path, data in layers:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists() and not path.is_file():
                raise IsADirectoryError(f"output path is not a regular file: {path}")

            serialized = serialize_json(data)
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{path.name}.",
                suffix=".tmp",
                dir=path.parent,
                text=True,
            )
            temporary_path = pathlib.Path(temporary_name)
            backup_path: pathlib.Path | None = None
            try:
                with os.fdopen(
                    descriptor,
                    "w",
                    encoding="utf-8",
                    newline="\n",
                ) as output:
                    output.write(serialized)
                    output.flush()
                    os.fsync(output.fileno())

                if path.is_file():
                    backup_descriptor, backup_name = tempfile.mkstemp(
                        prefix=f".{path.name}.",
                        suffix=".bak",
                        dir=path.parent,
                    )
                    os.close(backup_descriptor)
                    backup_path = pathlib.Path(backup_name)
                    shutil.copy2(path, backup_path)
                    shutil.copymode(path, temporary_path)

                prepared.append((path, temporary_path, backup_path))
            except Exception:
                temporary_path.unlink(missing_ok=True)
                if backup_path is not None:
                    backup_path.unlink(missing_ok=True)
                raise

        for path, temporary_path, backup_path in prepared:
            os.replace(temporary_path, path)
            replaced.append((path, backup_path))
    except BaseException as original_error:
        rollback_errors: list[str] = []
        for path, backup_path in reversed(replaced):
            try:
                if backup_path is None:
                    path.unlink(missing_ok=True)
                else:
                    try:
                        os.replace(backup_path, path)
                    except OSError:
                        shutil.copy2(backup_path, path)
            except BaseException as rollback_error:
                if backup_path is not None:
                    preserved_backups.add(backup_path)
                rollback_errors.append(f"{path}: {rollback_error}")
        if rollback_errors:
            message = "failed to roll back managed layers: " + "; ".join(
                rollback_errors
            )
            if preserved_backups:
                message += "; recovery backups preserved: " + ", ".join(
                    str(path) for path in sorted(preserved_backups)
                )
            raise OSError(message) from original_error
        raise
    finally:
        for _, temporary_path, backup_path in prepared:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
            if backup_path is not None and backup_path not in preserved_backups:
                try:
                    backup_path.unlink(missing_ok=True)
                except OSError:
                    pass


def repo_root() -> pathlib.Path:
    here = pathlib.Path(__file__).resolve()
    for candidate in (here, *here.parents):
        if (candidate / ".chezmoiroot").is_file() or (candidate / ".git").exists():
            return candidate
    return pathlib.Path.cwd()


def load_jsonc_object(path: pathlib.Path) -> dict[str, Any]:
    try:
        return parse_jsonc_object(path)
    except (OSError, UnicodeError) as exc:
        fail(f"Error: failed to read {path}: {exc}")
    except JsoncError as exc:
        fail(f"Error: invalid JSONC in {path}:{exc.line}:{exc.column}: {exc}")


def default_live_paths() -> tuple[pathlib.Path, pathlib.Path]:
    home = pathlib.Path.home()
    if sys.platform == "darwin":
        base = home / "Library" / "Application Support"
        return (
            base / "Code" / "User" / "settings.json",
            base / "Cursor" / "User" / "settings.json",
        )
    cfg = home / ".config"
    return (
        cfg / "Code" / "User" / "settings.json",
        cfg / "Cursor" / "User" / "settings.json",
    )


def json_values_equal(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            json_values_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            json_values_equal(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=True)
        )
    return left == right


def classify(
    code: dict[str, Any],
    cursor: dict[str, Any],
    *,
    ignored: set[str],
    code_ignored: set[str],
    cursor_ignored: set[str],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    shared: dict[str, Any] = {}
    code_only: dict[str, Any] = {}
    cursor_only: dict[str, Any] = {}

    for key in sorted(set(code) | set(cursor)):
        in_code = key in code
        in_cursor = key in cursor
        skip_code = in_code and (key in ignored or key in code_ignored)
        skip_cursor = in_cursor and (key in ignored or key in cursor_ignored)

        if in_code and in_cursor:
            # Honor per-app ignores (same as apply): skip only the ignored side.
            if skip_code and skip_cursor:
                continue
            if skip_code:
                cursor_only[key] = cursor[key]
                continue
            if skip_cursor:
                code_only[key] = code[key]
                continue
            code_val = code[key]
            cursor_val = cursor[key]
            if json_values_equal(code_val, cursor_val):
                shared[key] = code_val
            elif (
                key == "yaml.disableSchemaDetection"
                and isinstance(code_val, list)
                and isinstance(cursor_val, list)
                and len(code_val) != len(cursor_val)
            ):
                shared[key] = (
                    code_val if len(code_val) > len(cursor_val) else cursor_val
                )
            else:
                code_only[key] = code_val
                cursor_only[key] = cursor_val
        elif in_code:
            if not skip_code:
                code_only[key] = code[key]
        elif not skip_cursor:
            cursor_only[key] = cursor[key]

    return shared, code_only, cursor_only


def generate_from_live(
    code_path: pathlib.Path,
    cursor_path: pathlib.Path,
    out_dir: pathlib.Path,
    *,
    dry_run: bool,
) -> None:
    code = load_jsonc_object(code_path)
    cursor = load_jsonc_object(cursor_path)

    ignored = load_ignored_keys(out_dir / "ignored.json")
    code_ignored = load_ignored_keys(out_dir / "code.ignored.json")
    cursor_ignored = load_ignored_keys(out_dir / "cursor.ignored.json")

    shared, code_only, cursor_only = classify(
        code,
        cursor,
        ignored=ignored,
        code_ignored=code_ignored,
        cursor_ignored=cursor_ignored,
    )

    print(
        f"shared={len(shared)} code={len(code_only)} cursor={len(cursor_only)} "
        f"ignored={len(ignored)} code.ignored={len(code_ignored)} "
        f"cursor.ignored={len(cursor_ignored)}"
    )

    if dry_run:
        print(f"dry-run: would write under {out_dir}")
        return

    write_json_layers(
        [
            (out_dir / "shared.json", shared),
            (out_dir / "code.json", code_only),
            (out_dir / "cursor.json", cursor_only),
        ]
    )
    print(f"wrote managed layers under {out_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate shared.json, code.json, and cursor.json from live Code/Cursor "
            "User settings. Ignored keys are read from existing *.ignored.json files."
        ),
    )
    parser.add_argument(
        "--code",
        type=pathlib.Path,
        help="Path to VS Code User settings.json (default: platform live path)",
    )
    parser.add_argument(
        "--cursor",
        type=pathlib.Path,
        help="Path to Cursor User settings.json (default: platform live path)",
    )
    parser.add_argument(
        "--out",
        type=pathlib.Path,
        default=None,
        help="Output directory (default: <repo>/home/dot_config/vscode-settings)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print counts without writing files",
    )
    args = parser.parse_args()

    default_code, default_cursor = default_live_paths()
    code_path = args.code or default_code
    cursor_path = args.cursor or default_cursor
    out_dir = args.out or (repo_root() / "home" / "dot_config" / "vscode-settings")

    if code_path.is_symlink() or not code_path.is_file():
        fail(f"Error: Code settings is not a regular file: {code_path}")
    if cursor_path.is_symlink() or not cursor_path.is_file():
        fail(f"Error: Cursor settings is not a regular file: {cursor_path}")

    try:
        generate_from_live(code_path, cursor_path, out_dir, dry_run=args.dry_run)
    except (OSError, ValueError) as exc:
        fail(
            f"Error: failed to write managed layers under {out_dir}: {exc}",
            code=EXIT_OPERATIONAL,
        )


if __name__ == "__main__":
    main()
