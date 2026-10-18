"""Check the Fish entry point with an absent or existing uv binary."""

import os
import shlex
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FISH = shutil.which("fish")


@unittest.skipUnless(FISH, "fish is required")
class BootstrapTests(unittest.TestCase):
    def run_apply(self, *, installed=False, install_status=0, run_status=0):
        with tempfile.TemporaryDirectory(prefix="codex bootstrap ") as directory:
            root = Path(directory)
            binary = root / ".local/bin/uv"
            binary.parent.mkdir(parents=True)
            stub = root / "uv-stub"
            stub.write_text(
                '#!/bin/sh\nprintf "%s\\n" "$@" > "$HOME/uv-args"\n'
                'exit "$UV_RUN_STATUS"\n'
            )
            stub.chmod(0o755)
            if installed:
                shutil.copy2(stub, binary)
            script = "\n".join(
                "source " + shlex.quote(str(ROOT / path))
                for path in (
                    "home/dot_config/fish/exact_conf.d/00-core-functions.fish",
                    "home/dot_config/fish/exact_functions/exact_unix/uv.fish",
                    "home/dot_config/fish/exact_functions/exact_unix/codex-settings-apply.fish",
                )
            )
            script += """
function __uv_install
    echo install >>"$HOME/install-calls"
    test "$UV_INSTALL_STATUS" -eq 0; or return $UV_INSTALL_STATUS
    /bin/cp "$HOME/uv-stub" "$argv[1]"
end
codex-settings-apply --dry-run
"""
            result = subprocess.run(
                [str(FISH), "--no-config", "-c", script],
                env={
                    **os.environ,
                    "HOME": directory,
                    "PATH": str(root / "empty-bin"),
                    "UV_INSTALL_STATUS": str(install_status),
                    "UV_RUN_STATUS": str(run_status),
                },
                capture_output=True,
                text=True,
                check=False,
            )
            installed_now = (root / "install-calls").exists()
            args = root / "uv-args"
            forwarded = args.read_text().splitlines() if args.exists() else []
            expected = [
                "run",
                "--script",
                str(root / ".local/share/chezmoi/app-settings/codex/apply.py"),
                "--dry-run",
            ]
            return result, installed_now, forwarded, expected

    def test_first_use_installs_uv_and_existing_binary_is_reused(self):
        for installed in (False, True):
            with self.subTest(installed=installed):
                result, installed_now, forwarded, expected = self.run_apply(
                    installed=installed
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(installed_now, not installed)
                self.assertEqual(forwarded, expected)

    def test_install_and_helper_failures_reach_the_caller(self):
        result, _, forwarded, _ = self.run_apply(install_status=7)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(forwarded, [])
        result, _, _, _ = self.run_apply(run_status=9)
        self.assertEqual(result.returncode, 9, result.stderr)


if __name__ == "__main__":
    unittest.main()
