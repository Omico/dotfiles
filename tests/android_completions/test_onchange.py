"""Verify chezmoi onchange scheduling in isolated macOS and Linux destinations."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHEZMOI = shutil.which("chezmoi")
FISH = shutil.which("fish")
SCRIPT = "run_onchange_after_95-android-completions.fish.tmpl"


@unittest.skipUnless(CHEZMOI and FISH, "chezmoi and fish are required")
class OnchangeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="android-onchange-tests-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.destination = self.root / "destination"
        self.source.mkdir()
        self.destination.mkdir()
        self.binaries = self.root / "bin"
        self.binaries.mkdir()
        (self.binaries / "fish").symlink_to(str(FISH))
        (self.binaries / "python3").write_text("#!/bin/sh\nexit 9\n")
        (self.binaries / "python3").chmod(0o755)
        uv = self.binaries / "uv"
        uv.write_text(
            f"#!{sys.executable}\n"
            "import os, sys\n"
            "expected = ['run', '--quiet', '--no-project', '--managed-python', '--no-python-downloads', '--python', '3.13', '--script']\n"
            "if sys.argv[1:1+len(expected)] != expected: sys.exit(9)\n"
            "os.execv(sys.executable, [sys.executable, *sys.argv[1+len(expected):]])\n"
        )
        uv.chmod(0o755)
        android = self.binaries / "android"
        android.write_text(
            '#!/bin/sh\n[ "$1" = --version ] || exit 9\nprintf "%s\\n" "$ANDROID_TEST_VERSION"\n'
        )
        android.chmod(0o755)
        shutil.copy(ROOT / "home" / SCRIPT, self.source / SCRIPT)
        shutil.copy(
            ROOT / "home/.chezmoiignore.tmpl", self.source / ".chezmoiignore.tmpl"
        )
        self.helper = self.root / "scripts/android-fish-completions.py"
        self.helper.parent.mkdir(parents=True)
        self.helper.write_text(
            "import os, pathlib, sys\n"
            'root = pathlib.Path(os.environ["HOME"])\n'
            'with (root / "generation-calls").open("a") as f: f.write("generate\\n")\n'
            'if os.environ.get("ANDROID_TEST_FAIL"): sys.exit(4)\n'
            'target = pathlib.Path(sys.argv[sys.argv.index("--output") + 1])\n'
            "target.parent.mkdir(parents=True, exist_ok=True)\n"
            'target.write_text("# Generated " + os.environ["ANDROID_TEST_VERSION"] + "\\n")\n'
        )
        self.config = self.root / "config.toml"
        self.config.write_text("")
        self.target = self.destination / ".config/fish/completions/android.fish"

    def apply(self, platform="linux", version="1", fail=False):
        return subprocess.run(
            [
                str(CHEZMOI),
                "--source",
                str(self.source),
                "--destination",
                str(self.destination),
                "--config",
                str(self.config),
                "--persistent-state",
                str(self.root / "state.db"),
                "--override-data",
                json.dumps({"chezmoi": {"os": platform}}),
                "apply",
            ],
            env={
                **os.environ,
                "HOME": str(self.destination),
                "XDG_CONFIG_HOME": str(self.destination / ".config"),
                "PATH": f"{self.binaries}:/usr/bin:/bin",
                "ANDROID_TEST_VERSION": version,
                "ANDROID_TEST_FAIL": "1" if fail else "",
            },
            text=True,
            capture_output=True,
            check=False,
        )

    def call_count(self):
        log = self.destination / "generation-calls"
        return len(log.read_text().splitlines()) if log.exists() else 0

    def check_changes(self, platform):
        for version, expected in [("1", 1), ("1", 1), ("2", 2)]:
            result = self.apply(platform=platform, version=version)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(self.call_count(), expected)
            self.assertEqual(self.target.read_text(), f"# Generated {version}\n")
        self.helper.write_text(self.helper.read_text() + "# Generator changed\n")
        result = self.apply(platform=platform, version="2")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.call_count(), 3)

    def test_linux_version_and_generator_changes(self):
        self.check_changes("linux")

    def test_macos_version_and_generator_changes(self):
        self.check_changes("darwin")

    def test_repository_source_root_with_special_characters(self):
        repository = self.root / "repository 'with \\ spaces"
        repository.mkdir()
        (repository / ".chezmoiroot").write_text("home\n")
        self.source.rename(repository / "home")
        self.helper.parent.rename(repository / "scripts")
        self.source = repository
        self.helper = repository / "scripts/android-fish-completions.py"
        self.check_changes("linux")

    def test_cli_found_only_after_fish_startup_is_refreshed(self):
        local_bin = self.destination / ".local/bin"
        local_bin.mkdir(parents=True)
        shutil.move(self.binaries / "android", local_bin / "android")
        conf = self.source / "dot_config/fish/conf.d"
        conf.mkdir(parents=True)
        for name in ("00-core-functions.fish", "10-common.fish"):
            shutil.copy(ROOT / "home/dot_config/fish/exact_conf.d" / name, conf / name)
        self.check_changes("linux")

    def test_failure_is_retried_and_existing_file_is_preserved(self):
        self.assertEqual(self.apply().returncode, 0)
        before = self.target.read_bytes()
        self.assertNotEqual(self.apply(version="2", fail=True).returncode, 0)
        self.assertEqual(self.target.read_bytes(), before)
        self.assertEqual(self.apply(version="2").returncode, 0)
        self.assertEqual(self.call_count(), 3)

    def test_missing_cli_and_unsupported_platform_skip_generation(self):
        self.assertEqual(self.apply(platform="windows").returncode, 0)
        self.assertEqual(self.call_count(), 0)
        (self.binaries / "android").unlink()
        self.assertEqual(self.apply().returncode, 0)
        self.assertEqual(self.call_count(), 0)

    def test_missing_uv_preserves_existing_completions(self):
        self.assertEqual(self.apply().returncode, 0)
        before = self.target.read_bytes()
        (self.binaries / "uv").unlink()
        result = self.apply(version="2")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("uv is required", result.stderr)
        self.assertEqual(self.target.read_bytes(), before)
