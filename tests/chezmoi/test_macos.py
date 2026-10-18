"""Verify macOS setup failures without running real system commands."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class MacosTests(unittest.TestCase):
    def test_required_steps_stop_on_failure(self):
        for failed_step in (
            "osascript",
            "sudo:-v",
            "defaults:com.apple.finder",
            "sudo:cp",
            "sudo:sed",
            "",
        ):
            with (
                self.subTest(failed_step=failed_step),
                tempfile.TemporaryDirectory(prefix="macos-setup-") as directory,
            ):
                root = Path(directory)
                environment = root / "bash-env"
                environment.write_text(
                    'record() {\n printf "%s\\n" "$1" >> "$HOME/calls"\n'
                    ' [[ "$1" != "$FAIL_STEP" ]] || return 7\n}\n'
                    'sudo() { [[ "$1" != -n ]] || return 1; record "sudo:$1"; }\n'
                    'defaults() { record "defaults:$2"; }\n'
                    "osascript() { record osascript; }\n"
                    "sleep() { return 0; }\nkill() { return 1; }\n"
                )
                result = subprocess.run(
                    ["/bin/bash", str(ROOT / "macos")],
                    env={
                        **os.environ,
                        "HOME": directory,
                        "BASH_ENV": str(environment),
                        "FAIL_STEP": failed_step,
                    },
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )
                self.assertEqual(
                    result.returncode, 7 if failed_step else 0, result.stderr
                )
                calls = (root / "calls").read_text().splitlines()
                self.assertEqual(calls[-1], failed_step or "defaults:-g")


if __name__ == "__main__":
    unittest.main()
