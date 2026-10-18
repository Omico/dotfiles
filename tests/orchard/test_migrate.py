"""Exercise migration exit states without changing installed applications."""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FISH = shutil.which("fish")


@unittest.skipUnless(FISH, "fish is required")
class MigrationTests(unittest.TestCase):
    def run_migration(self, *, query=0, uninstall=0, install=0, plan=False):
        with tempfile.TemporaryDirectory(prefix="orchard-migrate-") as directory:
            root = Path(directory)
            apps = root / "config/orchard/apps"
            apps.mkdir(parents=True)
            for app in ("failed", "successful"):
                (apps / f"{app}.fish").write_text("")
            binaries = root / "bin"
            binaries.mkdir()
            for name, body in {
                "brew": """case "$1" in
outdated)
    [ "$query_status" -eq 0 ] || { echo 'query failed' >&2; exit "$query_status"; }
    printf 'failed\\nsuccessful\\nmissing\\n';;
uninstall)
    echo "uninstall $3" >> "$HOME/calls"
    [ "$3" != failed ] || exit "$uninstall_status";;
esac
""",
                "orchard": """echo "install $2" >> "$HOME/calls"
[ "$2" != failed ] || exit "$install_status"
exit 0
""",
            }.items():
                target = binaries / name
                target.write_text("#!/bin/sh\n" + body)
                target.chmod(0o755)
            result = subprocess.run(
                [
                    str(FISH),
                    "--no-config",
                    str(ROOT / "home/dot_local/bin/executable_orchard"),
                    "migrate",
                    "brew",
                    *(["--plan"] if plan else []),
                ],
                env={
                    **os.environ,
                    "HOME": directory,
                    "XDG_CONFIG_HOME": str(root / "config"),
                    "PATH": str(binaries) + os.pathsep + os.environ["PATH"],
                    "query_status": str(query),
                    "uninstall_status": str(uninstall),
                    "install_status": str(install),
                },
                capture_output=True,
                text=True,
                check=False,
            )
            calls = root / "calls"
            return result, calls.read_text() if calls.exists() else ""

    def test_query_failure_is_not_an_empty_plan(self):
        result, calls = self.run_migration(query=8)
        self.assertEqual(result.returncode, 8)
        self.assertIn("query failed", result.stderr)
        self.assertNotIn("No outdated", result.stdout)
        self.assertEqual(calls, "")

    def test_partial_failures_survive_later_success_and_missing_report(self):
        for failed_stage in ("uninstall", "install"):
            with self.subTest(stage=failed_stage):
                result, calls = self.run_migration(
                    uninstall=9 if failed_stage == "uninstall" else 0,
                    install=9 if failed_stage == "install" else 0,
                )
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn("install successful", calls)
                self.assertIn("missing", result.stdout)
                if failed_stage == "uninstall":
                    self.assertNotIn("install failed", calls.splitlines())

    def test_success_and_plan_return_zero(self):
        result, calls = self.run_migration()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("install failed", calls)
        result, calls = self.run_migration(plan=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, "")


if __name__ == "__main__":
    unittest.main()
