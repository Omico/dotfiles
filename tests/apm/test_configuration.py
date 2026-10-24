"""Exercise APM environment selection and merges without a terminal or account."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FISH = shutil.which("fish")
SOURCE = ROOT / "home/dot_config/fish/exact_conf.d/99-apm.fish"


@unittest.skipUnless(FISH and shutil.which("yq"), "fish and yq are required")
class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="apm-configuration-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.sources = self.root / "dot_apm"
        self.sources.mkdir()
        for name, package in {
            "base": "shared/package",
            "external": "external/package",
            "internal": "internal/package",
            "custom": "local/custom",
        }.items():
            (self.sources / f"apm.{name}.yml").write_text(
                f"dependencies:\n  apm: [{package}]\n"
            )
        self.selector = self.sources / "apm.environment"
        self.runtime = self.root / "runtime/apm.yml"
        binaries = self.root / "bin"
        binaries.mkdir()
        gh = binaries / "gh"
        gh.write_text(
            '#!/bin/sh\necho called >> "$HOME/gh-calls"\nprintf "%s\\n" "$TEST_LOGIN"\nexit "$TEST_GH_STATUS"\n'
        )
        gh.chmod(0o755)
        self.env = {
            **os.environ,
            "HOME": str(self.root),
            "TMPDIR": str(self.root),
            "PATH": str(binaries) + os.pathsep + os.environ["PATH"],
        }

    def run_fish(self, operation="__apm-merge-source-config", *, login="", status=1):
        return subprocess.run(
            [
                str(FISH),
                "--no-config",
                "-c",
                """source "$argv[1]"
set -g __apm_home "$HOME/runtime"
function chezmoi
    echo "$HOME"
end
"""
                + operation,
                str(SOURCE),
            ],
            env={**self.env, "TEST_LOGIN": login, "TEST_GH_STATUS": str(status)},
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )

    def packages(self, path):
        result = subprocess.run(
            ["yq", "-o=json", ".dependencies.apm", str(path)],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)

    def test_failed_account_detection_does_not_save_selection(self):
        for login in ("", "null"):
            with self.subTest(login=login):
                result = self.run_fish(login=login)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(self.selector.exists())
                self.assertFalse(self.runtime.exists())

    def test_account_detection_selects_the_environment(self):
        for login, expected in (
            ("Omico", "internal"),
            ("omico", "internal"),
            ("SomeoneElse", "external"),
        ):
            with self.subTest(login=login):
                result = self.run_fish(login=login, status=0)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.selector.read_text().strip(), expected)
                self.selector.unlink()

    def test_saved_selection_preserves_custom_settings_without_account_queries(self):
        self.selector.write_text("external\n")
        result = self.run_fish()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.packages(self.runtime),
            ["external/package", "local/custom", "shared/package"],
        )
        paths = self.run_fish("__apm-require-source-paths")
        self.assertEqual(paths.returncode, 0, paths.stderr)
        self.assertEqual(
            paths.stdout.splitlines()[1], str(self.sources / "apm.custom.yml")
        )

        self.selector.write_text("internal\n")
        result = self.run_fish()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.packages(self.runtime),
            ["internal/package", "local/custom", "shared/package"],
        )
        previous = self.runtime.read_bytes()
        result = self.run_fish()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.runtime.read_bytes(), previous)

        self.selector.write_text("invalid\n")
        result = self.run_fish()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.runtime.read_bytes(), previous)

        self.selector.write_text("external\n")
        result = self.run_fish()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.packages(self.runtime),
            ["external/package", "local/custom", "shared/package"],
        )
        self.assertEqual(
            self.packages(self.sources / "apm.custom.yml"), ["local/custom"]
        )
        self.assertFalse((self.root / "gh-calls").exists())
