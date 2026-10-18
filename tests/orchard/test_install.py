"""Exercise app replacement and download failures without sudo or real installs."""

import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FISH = shutil.which("fish")
ORCHARD = ROOT / "home/dot_local/bin/executable_orchard"
APPS = ROOT / "home/dot_config/exact_orchard/exact_apps"

SUDO_STUB = """import os, shutil, subprocess, sys
from pathlib import Path
command, *args = sys.argv[1:]
root = Path(os.environ['HOME'])
assert command in ('mkdir', 'mktemp', 'ditto', 'mv', 'rm')
assert all(arg.startswith('-') or Path(arg).resolve().is_relative_to(root.resolve()) for arg in args), args
fault = os.environ.get('fault', '')
if command == 'ditto':
    if fault == 'copy':
        Path(args[1]).mkdir()
        (Path(args[1]) / 'partial').write_text('incomplete')
        sys.exit(28)
    shutil.copytree(args[0], args[1], symlinks=True)
    sys.exit(0)
if command == 'mv':
    source = Path(args[0])
    if source.name == 'Demo.app' and fault == 'backup':
        sys.exit(29)
    if source.name == 'new.app' and fault in ('promote', 'restore'):
        sys.exit(30)
    if source.name == 'previous.app' and fault == 'restore':
        sys.exit(31)
sys.exit(subprocess.run([shutil.which(command), *args]).returncode)
"""


@unittest.skipUnless(FISH, "fish is required")
class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="orchard-install-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.binaries = self.root / "bin"
        self.binaries.mkdir()
        self.library = self.root / "orchard.fish"
        self.library.write_text(ORCHARD.read_text().split("# Main entry\n")[0])
        self.env = {
            **os.environ,
            "HOME": str(self.root),
            "XDG_CONFIG_HOME": str(self.root / "config"),
            "XDG_CACHE_HOME": str(self.root / "cache"),
            "TMPDIR": str(self.root),
            "PATH": str(self.binaries) + os.pathsep + os.environ["PATH"],
        }

    def run_fish(self, script, **env):
        return subprocess.run(
            [
                str(FISH),
                "--no-config",
                "-c",
                f"source {shlex.quote(str(self.library))}\n" + script,
            ],
            env={**self.env, **env},
            text=True,
            capture_output=True,
            check=False,
        )

    def run_install(self, archive_type, fault="", *, existing=True):
        fixture = self.root / "source/Demo.app"
        fixture.mkdir(parents=True, exist_ok=True)
        (fixture / "new").write_text("replacement")
        target = self.root / "Applications with spaces/Demo.app"
        target.parent.mkdir(exist_ok=True)
        if target.exists():
            shutil.rmtree(target)
        if existing:
            target.mkdir()
            (target / "old").write_text("working")
        sudo = self.binaries / "sudo"
        sudo.write_text(f"#!{sys.executable}\n" + SUDO_STUB)
        sudo.chmod(0o755)
        archive = self.root / "fixture.zip"
        with zipfile.ZipFile(archive, "w") as zipped:
            zipped.write(fixture / "new", "Demo.app/new")
        command = (
            '_orchard_dmg_install_app "$HOME/source"'
            if archive_type == "dmg"
            else "_orchard_install_zip"
        )
        result = self.run_fish(
            'function mktemp; command mktemp -d "$HOME/extract.XXXXXX"; end\n'
            "set -g orchard_app_bundle_name Demo.app\n"
            "set -g orchard_app_display_name Demo\n"
            'set -g orchard_app_bundle_path "$HOME/Applications with spaces/Demo.app"\n'
            'set -g _orchard_app_archive_cache_path "$HOME/fixture.zip"\n' + command,
            fault=fault,
        )
        return result, target

    def test_replacement_failures_preserve_the_original_bundle(self):
        for archive_type in ("dmg", "zip"):
            for fault, status in (("copy", 28), ("backup", 29), ("promote", 30)):
                with self.subTest(archive_type=archive_type, fault=fault):
                    result, target = self.run_install(archive_type, fault)
                    self.assertEqual(result.returncode, status, result.stderr)
                    self.assertEqual((target / "old").read_text(), "working")
                    self.assertFalse((target / "new").exists())
                    self.assertEqual(list(target.parent.glob(".orchard-install.*")), [])

    def test_failed_restore_retains_and_reports_the_backup(self):
        result, target = self.run_install("dmg", "restore")
        self.assertEqual(result.returncode, 30, result.stderr)
        backups = list(target.parent.glob(".orchard-install.*/previous.app/old"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), "working")
        self.assertIn(str(backups[0].parent), result.stderr)

    def test_new_install_and_reinstall_replace_without_merging_old_files(self):
        for archive_type in ("dmg", "zip"):
            for existing in (False, True):
                with self.subTest(archive_type=archive_type, existing=existing):
                    result, target = self.run_install(archive_type, existing=existing)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual((target / "new").read_text(), "replacement")
                    self.assertFalse((target / "old").exists())
                    self.assertEqual(list(target.parent.glob(".orchard-install.*")), [])

    def test_download_failure_stops_fresh_and_resumed_archive_preparation(self):
        aria = self.binaries / "aria2c"
        aria.write_text('#!/bin/sh\nexit "$download_status"\n')
        aria.chmod(0o755)
        cache = self.root / "cache/orchard"
        cache.mkdir(parents=True)
        prelude = (
            "set -g orchard_app_download_url https://example.invalid/app.zip\n"
            "set -g orchard_app_display_name Demo\n"
            "set -g orchard_app_download_type zip\n"
            'set -g _orchard_app_archive_cache_path "$HOME/cache/orchard/demo.zip"\n'
        )
        for resumed in (False, True):
            if resumed:
                (cache / "demo.zip").write_bytes(b"partial")
                (cache / "demo.zip.aria2").touch()
            result = self.run_fish(
                prelude + "_orchard_download_archive", download_status="7"
            )
            self.assertEqual(result.returncode, 7, result.stderr)
            result = self.run_fish(
                prelude + "_orchard_ensure_archive", download_status="7"
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Download failed", result.stderr)
        result = self.run_fish(
            prelude + "_orchard_download_archive", download_status="0"
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_defaults_preserve_explicit_paths_and_reset_between_packages(self):
        result = self.run_fish(
            "set -g orchard_app_display_name Demo\n"
            'set -g orchard_app_bundle_path "$HOME/custom/Demo.app"\n'
            "_orchard_apply_app_defaults\n"
            'echo "$orchard_app_bundle_path"\n'
            "_orchard_clear_app_state\n"
            "set -g orchard_app_display_name Other\n"
            "_orchard_apply_app_defaults\n"
            'echo "$orchard_app_bundle_path"\n'
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.splitlines(),
            [str(self.root / "custom/Demo.app"), "/Applications/Other.app"],
        )

    def resolve(self, app, metadata, *, curl_status="0"):
        (self.root / "metadata").write_text(metadata)
        return self.run_fish(
            'function curl; cat "$HOME/metadata"; return $curl_status; end\n'
            f"source {shlex.quote(str(APPS / (app + '.fish')))}\n"
            "orchard_resolve_download_url_callback; or exit $status\n"
            'printf "%s\\n" "$orchard_app_download_url"',
            curl_status=curl_status,
        )

    def test_microsoft_auto_update_skips_an_existing_bundle(self):
        apps = self.root / "config/orchard/apps"
        apps.mkdir(parents=True)
        bundle = self.root / "Microsoft/MAU2.0/Microsoft AutoUpdate.app"
        bundle.mkdir(parents=True)
        package = (
            (APPS / "microsoft-auto-update.fish")
            .read_text()
            .replace(
                "/Library/Application Support/Microsoft/MAU2.0/Microsoft AutoUpdate.app",
                str(bundle),
            )
        )
        (apps / "microsoft-auto-update.fish").write_text(package)
        aria = self.binaries / "aria2c"
        aria.write_text("#!/bin/sh\necho unexpected-download >&2\nexit 91\n")
        aria.chmod(0o755)
        result = self.run_fish("_orchard_cmd_install install microsoft-auto-update")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Microsoft AutoUpdate is already installed", result.stdout)
        self.assertNotIn("unexpected-download", result.stderr)

    def test_wireshark_resolver_produces_a_single_url_from_upstream_metadata(self):
        result = self.resolve(
            "wireshark-app",
            '<enclosure sparkle:shortVersionString="4.6.9" url="unused"/>',
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.strip(),
            "https://www.wireshark.org/download/osx/all-versions/Wireshark%204.6.9.dmg",
        )

    def test_wireshark_resolver_rejects_fetch_failures_and_invalid_metadata(self):
        for metadata, curl_status in (
            ("", "0"),
            ("error", "22"),
            ('sparkle:shortVersionString="bad version"', "0"),
            (
                'sparkle:shortVersionString="4.6.9"\nsparkle:shortVersionString="4.6.8"',
                "0",
            ),
        ):
            result = self.resolve("wireshark-app", metadata, curl_status=curl_status)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertTrue(result.stderr)


if __name__ == "__main__":
    unittest.main()
