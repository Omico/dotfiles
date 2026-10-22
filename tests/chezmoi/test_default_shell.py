"""Verify login shell setup without changing the host account or shell registry."""

import json
import os
import shlex
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FISH = shutil.which("fish")
CHEZMOI = shutil.which("chezmoi")


@unittest.skipUnless(FISH and CHEZMOI, "fish and chezmoi are required")
class DefaultShellTests(unittest.TestCase):
    def run_setup(
        self,
        platform,
        *,
        current=False,
        registered=False,
        failure="",
        account_record=None,
    ):
        with tempfile.TemporaryDirectory(prefix="default-shell-") as directory:
            root = Path(directory)
            binaries = root / "bin"
            binaries.mkdir()
            fish_path = str(binaries / "fish")
            (binaries / "fish").symlink_to(str(FISH))
            shell = fish_path if current else "/bin/sh"
            record = (
                account_record
                if account_record is not None
                else f"testuser:x:1000:1000:Test:/home/testuser:{shell}"
            )
            bodies = {
                "id": "echo testuser\n",
                "getent": f"printf '%s\\n' {shlex.quote(record)}\n",
                "dscl": f"echo 'UserShell: {shell}'\n",
                "cat": f"printf '%s\\n' /bin/sh '{fish_path if registered else '/bin/bash'}'\n",
                "sudo": """case "$1" in
tee) read -r shell; printf '%s\\n' "$shell" > "$HOME/registered";;
chsh) test "$2" = -s && test "$4" = testuser || exit 99;;
*) exit 98;;
esac
""",
            }
            for name, body in bodies.items():
                binary = binaries / name
                binary.write_text(
                    f'#!/bin/sh\necho "{name} $*" >> "$HOME/calls"\n'
                    f'[ "{name}" != "$FAIL_STEP" ] || exit 7\n'
                    + (
                        '[ "sudo:$1" != "$FAIL_STEP" ] || exit 7\n'
                        if name == "sudo"
                        else ""
                    )
                    + body
                )
                binary.chmod(0o755)
            if failure == "empty-account":
                (binaries / ("dscl" if platform == "darwin" else "getent")).write_text(
                    "#!/bin/sh\nexit 0\n"
                )
            config = root / "chezmoi.toml"
            config.write_text("")
            render = subprocess.run(
                [
                    str(CHEZMOI),
                    "--source",
                    str(ROOT),
                    "--config",
                    str(config),
                    "--override-data",
                    json.dumps({"chezmoi": {"os": platform}}),
                    "execute-template",
                    "--file",
                    str(ROOT / "home/run_once_after_30-default-shell.fish.tmpl"),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            result = subprocess.run(
                [str(FISH), "--no-config"],
                input=render.stdout,
                env={
                    **os.environ,
                    "HOME": directory,
                    "PATH": str(binaries),
                    "FAIL_STEP": failure,
                },
                capture_output=True,
                text=True,
                check=False,
            )
            calls = root / "calls"
            registered_path = root / "registered"
            return (
                result,
                calls.read_text().splitlines() if calls.exists() else [],
                registered_path.read_text() if registered_path.exists() else "",
                fish_path,
            )

    def test_current_account_and_registry_control_changes(self):
        for platform in ("darwin", "linux"):
            for current in (False, True):
                for registered in (False, True):
                    with self.subTest(
                        platform=platform, current=current, registered=registered
                    ):
                        result, calls, written, fish_path = self.run_setup(
                            platform, current=current, registered=registered
                        )
                        self.assertEqual(result.returncode, 0, result.stderr)
                        self.assertEqual(
                            written, "" if registered else fish_path + "\n"
                        )
                        self.assertEqual(
                            f"sudo chsh -s {fish_path} testuser" in calls, not current
                        )

    def test_failures_stop_before_later_changes(self):
        for platform, query in (("darwin", "dscl"), ("linux", "getent")):
            for failure in (
                "id",
                query,
                "empty-account",
                "cat",
                "sudo:tee",
                "sudo:chsh",
            ):
                with self.subTest(platform=platform, failure=failure):
                    result, calls, written, _ = self.run_setup(
                        platform, failure=failure
                    )
                    self.assertEqual(
                        result.returncode,
                        1 if failure == "empty-account" else 7,
                        result.stderr,
                    )
                    if failure != "sudo:chsh":
                        self.assertFalse(
                            any(call.startswith("sudo chsh") for call in calls)
                        )
                        self.assertEqual(written, "")

    def test_linux_empty_shell_still_switches_to_fish(self):
        for registered in (False, True):
            with self.subTest(registered=registered):
                result, calls, written, fish_path = self.run_setup(
                    "linux",
                    registered=registered,
                    account_record="testuser:x:1000:1000:Test:/home/testuser:",
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"sudo chsh -s {fish_path} testuser", calls)
                self.assertEqual(written, "" if registered else fish_path + "\n")

    def test_linux_invalid_account_stops_before_system_changes(self):
        for record in (
            "",
            "testuser:x:1000:1000:Test:/home/testuser",
            "other:x:1000:1000:Test:/home/testuser:",
            "testuser:x:1000:1000:Test:/home/testuser:/bin/sh:extra",
            (
                "testuser:x:1000:1000:Test:/home/testuser:\n"
                "testuser:x:1000:1000:Test:/home/testuser:/bin/sh"
            ),
        ):
            with self.subTest(record=record):
                result, calls, written, _ = self.run_setup(
                    "linux", account_record=record
                )
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertFalse(any(call.startswith("sudo ") for call in calls))
                self.assertEqual(written, "")

    def test_unsupported_platform_does_nothing(self):
        result, calls, written, _ = self.run_setup("windows")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, [])
        self.assertEqual(written, "")
