"""Validate package contracts through the Orchard CLI without installing apps."""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FISH = shutil.which("fish")
ORCHARD = ROOT / "home/dot_local/bin/executable_orchard"


@unittest.skipUnless(FISH, "fish is required")
class ValidationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="orchard-validate-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.apps = self.root / "config/orchard/apps"
        self.apps.mkdir(parents=True)

    def write_app(self, name, body):
        (self.apps / f"{name}.fish").write_text(body)

    def run_validate(self, *apps):
        return subprocess.run(
            [str(FISH), "--no-config", str(ORCHARD), "validate", *apps],
            env={
                **os.environ,
                "HOME": str(self.root),
                "XDG_CONFIG_HOME": str(self.root / "config"),
                "XDG_CACHE_HOME": str(self.root / "cache"),
                "TMPDIR": str(self.root),
            },
            capture_output=True,
            text=True,
            check=False,
        )

    def test_static_and_dynamic_packages_pass(self):
        self.write_app(
            "valid-static",
            """set -g orchard_app_id valid-static
set -g orchard_app_display_name "Valid Static"
set -g orchard_app_download_url "https://example.com/ValidStatic.dmg"
set -g orchard_app_download_type dmg
""",
        )
        self.write_app(
            "valid-dynamic",
            """set -g orchard_app_id valid-dynamic
set -g orchard_app_display_name "Valid Dynamic"
set -g orchard_app_download_type zip
function orchard_resolve_download_url_callback
    set -g orchard_app_download_url "https://example.com/ValidDynamic.zip"
end
""",
        )
        result = self.run_validate()
        self.assertEqual(result.returncode, 0, result.stderr)
        for expected in (
            "✓ valid-static",
            "✓ valid-dynamic",
            "✓ Validated 2 orchard app package(s).",
        ):
            self.assertIn(expected, result.stdout)

    def test_id_must_match_the_filename(self):
        self.write_app(
            "wrong-name",
            """set -g orchard_app_id other-name
set -g orchard_app_display_name "Wrong Name"
set -g orchard_app_download_url "https://example.com/WrongName.dmg"
set -g orchard_app_download_type dmg
""",
        )
        result = self.run_validate()
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("✗ wrong-name", result.stderr)
        self.assertIn("wrong-name: orchard_app_id must match filename", result.stderr)

    def test_missing_url_requires_a_resolver(self):
        self.write_app(
            "missing-url",
            """set -g orchard_app_id missing-url
set -g orchard_app_display_name "Missing URL"
set -g orchard_app_download_type dmg
""",
        )
        result = self.run_validate("missing-url")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("✗ missing-url", result.stderr)
        self.assertIn(
            "missing-url: orchard_app_download_url is required unless orchard_resolve_download_url_callback is defined",
            result.stderr,
        )

    def test_resolver_callbacks_do_not_leak_between_packages(self):
        self.write_app(
            "callback-first",
            """set -g orchard_app_id callback-first
set -g orchard_app_display_name "Callback First"
set -g orchard_app_download_type dmg
function orchard_resolve_download_url_callback
    set -g orchard_app_download_url "https://example.com/CallbackFirst.dmg"
end
""",
        )
        self.write_app(
            "missing-url",
            """set -g orchard_app_id missing-url
set -g orchard_app_display_name "Missing URL"
set -g orchard_app_download_type dmg
""",
        )
        result = self.run_validate()
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(
            "missing-url: orchard_app_download_url is required unless orchard_resolve_download_url_callback is defined",
            result.stderr,
        )
