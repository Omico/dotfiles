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
            "XDG_STATE_HOME": str(self.root / "state"),
            "TMPDIR": str(self.root),
            "PATH": str(self.binaries) + os.pathsep + os.environ["PATH"],
        }

    def run_fish(self, script, *, cwd=None, **env):
        return subprocess.run(
            [
                str(FISH),
                "--no-config",
                "-c",
                f"source {shlex.quote(str(self.library))}\n" + script,
            ],
            env={k: v for k, v in {**self.env, **env}.items() if v is not None},
            cwd=cwd,
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

    def test_state_directory_uses_absolute_override_or_default(self):
        default = str(self.root / ".local/state/orchard")
        custom = self.root / "custom state"
        for value, expected in (
            (None, default),
            ("", default),
            ("relative-state", default),
            (str(custom), str(custom / "orchard")),
        ):
            with self.subTest(value=value):
                result = self.run_fish(
                    'printf "%s\\n" "$_orchard_state_dir"', XDG_STATE_HOME=value
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), expected)

    def test_failed_callback_is_resumed_without_reinstalling_the_bundle(self):
        self.env["XDG_STATE_HOME"] = "relative-state"
        first_directory = self.root / "first"
        retry_directory = self.root / "retry"
        first_directory.mkdir()
        retry_directory.mkdir()
        apps = self.root / "config/orchard/apps"
        apps.mkdir(parents=True)
        (apps / "demo.fish").write_text(
            "set -g orchard_app_id demo\n"
            "set -g orchard_app_display_name Demo\n"
            "set -g orchard_app_download_url https://example.invalid/demo.zip\n"
            "set -g orchard_app_download_type zip\n"
            'set -g orchard_app_bundle_path "$HOME/Demo.app"\n'
            "function orchard_after_install_callback\n"
            ' echo callback >> "$HOME/calls"\n'
            ' test -e "$HOME/fail-callback"; and return 7\n'
            ' echo ready > "$HOME/cli"\n'
            "end\n"
        )
        script = (
            "function _orchard_ensure_archive\n"
            ' echo download >> "$HOME/calls"\nend\n'
            "function _orchard_install_zip\n"
            ' echo install >> "$HOME/calls"\n'
            ' mkdir -p "$orchard_app_bundle_path"\nend\n'
            "_orchard_cmd_install install demo\n"
        )
        failure = self.root / "fail-callback"
        failure.touch()
        pending = self.root / ".local/state/orchard/demo.after-install-pending"
        result = self.run_fish(script, cwd=first_directory)
        self.assertEqual(result.returncode, 7, result.stderr)
        self.assertTrue(pending.exists())
        self.assertEqual(pending.read_text(), "callback\n")
        self.assertFalse((self.root / "cli").exists())
        self.assertTrue((self.root / "Demo.app").is_dir())
        # Repeated failure keeps the recovery record and skips archive work.
        result = self.run_fish(script, cwd=retry_directory)
        self.assertEqual(result.returncode, 7, result.stderr)
        self.assertTrue(pending.exists())
        # Cleaning the download cache must not discard pending setup.
        self.assertEqual(self.run_fish("_orchard_cmd_cleanup").returncode, 0)
        failure.unlink()
        result = self.run_fish(script, cwd=retry_directory)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / "cli").read_text(), "ready\n")
        self.assertFalse(pending.exists())
        self.assertEqual(
            (self.root / "calls").read_text().splitlines(),
            ["download", "install", "callback", "callback", "callback"],
        )
        # Completed callbacks must not run again on an ordinary install.
        result = self.run_fish(script, cwd=first_directory)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / "calls").read_text().count("callback"), 3)

    def test_replacement_failures_preserve_the_original_bundle(self):
        for archive_type in ("dmg", "zip"):
            for fault, status in (("copy", 28), ("backup", 29), ("promote", 30)):
                with self.subTest(archive_type=archive_type, fault=fault):
                    result, target = self.run_install(archive_type, fault)
                    self.assertEqual(result.returncode, status, result.stderr)
                    self.assertEqual((target / "old").read_text(), "working")
                    self.assertFalse((target / "new").exists())
                    self.assertEqual(list(target.parent.glob(".orchard-install.*")), [])

    def test_partial_install_and_failed_force_retry_install_before_callback(self):
        apps = self.root / "config/orchard/apps"
        apps.mkdir(parents=True)
        (apps / "demo.fish").write_text(
            "set -g orchard_app_id demo\n"
            "set -g orchard_app_display_name Demo\n"
            "set -g orchard_app_download_url https://example.invalid/demo.pkg\n"
            "set -g orchard_app_download_type pkg\n"
            'set -g orchard_app_bundle_path "$HOME/Demo.app"\n'
            "function orchard_after_install_callback\n"
            " orchard_cli_wrapper demo Demo\nend\n"
        )
        script = r"""
function osascript; return 0; end
function _orchard_ensure_archive; return 0; end
function _orchard_install_pkg
    echo install >> "$HOME/install-calls"
    mkdir -p "$orchard_app_bundle_path"
    test -e "$HOME/fail-install"; and return 9
    mkdir -p "$orchard_app_bundle_path/Contents/MacOS"
    printf '#!/bin/sh\necho CLI-READY\n' > "$orchard_app_bundle_path/Contents/MacOS/Demo"
    chmod +x "$orchard_app_bundle_path/Contents/MacOS/Demo"
end
function sudo
    switch $argv[1]
        case mkdir
            return 0
        case tee
            cat > "$HOME/cli"
        case chmod
            command chmod +x "$HOME/cli"
        case '*'
            return 99
    end
end
_orchard_cmd_install install demo $force_arg
"""
        for existing in (False, True):
            with self.subTest(existing=existing):
                target = self.root / "Demo.app"
                shutil.rmtree(target, ignore_errors=True)
                if existing:
                    target.mkdir()
                    (target / "old").touch()
                for name in ("install-calls", "cli"):
                    (self.root / name).unlink(missing_ok=True)
                failure = self.root / "fail-install"
                failure.touch()
                result = self.run_fish(script, force_arg="--force" if existing else "")
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue(target.is_dir())
                self.assertFalse((self.root / "cli").exists())
                pending = self.root / "state/orchard/demo.after-install-pending"
                self.assertEqual(pending.read_text(), "installing\n")
                if existing:
                    # Earlier versions wrote empty markers before installation.
                    pending.write_text("")
                failure.unlink()
                result = self.run_fish(script, force_arg="")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(
                    (self.root / "install-calls").read_text().splitlines(),
                    ["install", "install"],
                )
                cli = subprocess.run(
                    [str(self.root / "cli")],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(cli.returncode, 0, cli.stderr)
                self.assertEqual(cli.stdout, "CLI-READY\n")
                self.assertFalse(pending.exists())

    def test_cleanup_reports_failure_and_handles_present_and_absent_cache(self):
        cache = self.root / "cache/orchard"
        cache.mkdir(parents=True)
        marker = cache / "archive"
        marker.write_text("cached")
        result = self.run_fish("function rm; return 23; end\n_orchard_cmd_cleanup")
        self.assertEqual(result.returncode, 23, result.stderr)
        self.assertNotIn("Cache cleared", result.stdout)
        self.assertTrue(marker.exists())
        result = self.run_fish("_orchard_cmd_cleanup")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Cache cleared", result.stdout)
        self.assertFalse(cache.exists())
        result = self.run_fish("_orchard_cmd_cleanup")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("already empty", result.stdout)

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
