"""Verify native cleanup and Rime file ownership in isolated destinations."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHEZMOI = shutil.which("chezmoi")
FISH = shutil.which("fish")


@unittest.skipUnless(CHEZMOI, "chezmoi is required")
class SourceStateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="chezmoi-source-state-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.destination = self.root / "destination"
        self.destination.mkdir()
        shutil.copytree(ROOT / "home", self.source / "home")
        shutil.copytree(ROOT / "rime", self.source / "rime")
        (self.source / ".chezmoiroot").write_text("home\n")
        self.config = self.root / "config/chezmoi.toml"
        self.config.parent.mkdir()
        self.config.write_text("")

    def run_chezmoi(self, *args, platform="darwin"):
        result = subprocess.run(
            [
                str(CHEZMOI),
                "--source",
                str(self.source),
                "--destination",
                str(self.destination),
                "--config",
                str(self.config),
                "--persistent-state",
                str(self.root / "state.boltdb"),
                "--cache",
                str(self.root / "cache"),
                "--override-data",
                json.dumps(
                    {
                        "chezmoi": {
                            "os": platform,
                            "kernel": {"osrelease": "6.8.0-generic"},
                            "osRelease": {"id": "ubuntu", "ubuntuCodename": "noble"},
                        }
                    }
                ),
                *args,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def write_target(self, name, contents="local\n"):
        target = self.destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(contents)
        return target

    def test_exact_cleanup_is_previewed_and_preserves_other_owners(self):
        stale = [
            self.write_target(f".config/{directory}/stale.txt")
            for directory in (
                "fish/conf.d",
                "fish/conf.d/unix",
                "fish/functions",
                "fish/functions/darwin",
                "ghostty",
                "ghostty/include",
                "orchard",
                "orchard/apps",
            )
        ]
        preserved = [
            self.write_target(name)
            for name in (
                ".config/fish/conf.d/apm.fish",
                ".config/fish/completions/local.fish",
                ".config/unrelated/local.conf",
                "Library/Rime/user.yaml",
                "Git/Mark24Code/rime-auto-deploy/custom/local.yaml",
            )
        ]
        preview = self.run_chezmoi(
            "apply", "--exclude=scripts", "--dry-run", "--verbose"
        )
        self.assertIn("deleted file", preview)
        self.assertTrue(all(path.exists() for path in stale))
        self.run_chezmoi("apply", "--exclude=scripts")
        self.assertTrue(all(not path.exists() for path in stale))
        self.assertTrue(all(path.read_text() == "local\n" for path in preserved))
        self.run_chezmoi("verify", "--exclude=scripts")

    def test_rime_changes_update_platform_user_directory(self):
        name = "default.custom.yaml"
        source = self.source / "rime" / name
        for platform, directory in (
            ("darwin", "Library/Rime"),
            ("linux", ".local/share/fcitx5/rime"),
        ):
            with self.subTest(platform=platform):
                self.run_chezmoi("apply", "--exclude=scripts", platform=platform)
                target = self.destination / directory / name
                self.assertEqual(target.read_bytes(), source.read_bytes())
                source.write_text(source.read_text() + "# Changed configuration\n")
                self.run_chezmoi("apply", "--exclude=scripts", platform=platform)
                self.assertEqual(target.read_bytes(), source.read_bytes())
                self.run_chezmoi("verify", "--exclude=scripts", platform=platform)
        self.assertFalse(
            (self.destination / "Git/Mark24Code/rime-auto-deploy").exists()
        )
        self.assertFalse(
            (
                self.destination / ".local/share/fcitx5/rime/squirrel.custom.yaml"
            ).exists()
        )

    def test_platform_filters_leave_unowned_rime_and_orchard_files(self):
        runtime = self.write_target("Library/Rime/default.custom.yaml")
        orchard = self.write_target(".config/orchard/apps/local.fish")
        self.run_chezmoi("apply", "--exclude=scripts", platform="linux")
        self.assertEqual(runtime.read_text(), "local\n")
        self.assertEqual(orchard.read_text(), "local\n")
        self.assertTrue(
            (
                self.destination / ".local/share/fcitx5/rime/default.custom.yaml"
            ).is_file()
        )

        self.run_chezmoi("apply", "--exclude=scripts", platform="windows")
        self.assertEqual(runtime.read_text(), "local\n")

    @unittest.skipUnless(FISH, "fish is required")
    def test_capture_keeps_exact_directories_and_records_local_deletions(self):
        fixtures = {
            "dot_config/fish/exact_conf.d/removed.fish": ".config/fish/conf.d/removed.fish",
            "dot_config/fish/exact_functions/exact_unix/removed.fish": ".config/fish/functions/unix/removed.fish",
            "dot_config/exact_ghostty/exact_include/removed.ghostty": ".config/ghostty/include/removed.ghostty",
        }
        for source in fixtures:
            path = self.source / "home" / source
            path.write_text("# Removed local file\n")
        changed_source = (
            self.source / "home/dot_config/fish/exact_functions/exact_unix/changed.fish"
        )
        changed_source.write_text("# Previously applied\n")
        self.run_chezmoi("apply", "--exclude=scripts")
        for target in fixtures.values():
            (self.destination / target).unlink()
        (self.destination / ".config/ghostty/config.ghostty").unlink()
        (self.destination / ".config/fish/conf.d/00-environment.fish").unlink()
        (self.destination / ".config/fish/functions/linux/grd-rdp.fish").unlink()
        (self.destination / ".config/fish/functions/unix/changed.fish").unlink()
        changed_source.write_text("# Source changes not yet applied\n")
        pending_sources = [
            self.source / "home" / name
            for name in (
                "dot_config/fish/exact_functions/pending.fish",
                "dot_config/fish/exact_functions/exact_unix/pending-scoped.fish",
                "dot_config/exact_ghostty/exact_include/pending.ghostty",
            )
        ]
        for source in pending_sources:
            source.write_text("# Source file not yet applied\n")
        self.write_target(".config/fish/conf.d/apm.fish", "# Installer-owned\n")
        before = sorted(
            str(path.relative_to(self.source))
            for path in self.source.rglob("exact_*")
            if path.is_dir()
        )
        result = subprocess.run(
            [
                str(FISH),
                "--no-config",
                "-c",
                """
set -g fish_platform darwin
source "$REVIEW_FUNCTION"
function chezmoi
    command "$REVIEW_CHEZMOI" --source "$REVIEW_SOURCE" --destination "$HOME" \
        --config "$REVIEW_CONFIG" --persistent-state "$REVIEW_STATE" $argv
end
chezmoi_add_configs
""",
            ],
            env={
                **os.environ,
                "HOME": str(self.destination),
                "REVIEW_FUNCTION": str(
                    self.source
                    / "home/dot_config/fish/exact_functions/exact_unix/chezmoi.fish"
                ),
                "REVIEW_CHEZMOI": str(CHEZMOI),
                "REVIEW_SOURCE": str(self.source),
                "REVIEW_CONFIG": str(self.config),
                "REVIEW_STATE": str(self.root / "state.boltdb"),
            },
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Keeping source file not yet applied:", result.stdout)
        self.assertIn("Keeping source changes not yet applied:", result.stdout)
        for source in pending_sources:
            self.assertEqual(source.read_text(), "# Source file not yet applied\n")
        self.assertEqual(
            changed_source.read_text(), "# Source changes not yet applied\n"
        )
        after = sorted(
            str(path.relative_to(self.source))
            for path in self.source.rglob("exact_*")
            if path.is_dir()
        )
        self.assertEqual(before, after)
        self.run_chezmoi("apply", "--exclude=scripts", "--force")
        for target in fixtures.values():
            self.assertFalse((self.destination / target).exists())
        self.assertFalse((self.destination / ".config/ghostty/config.ghostty").exists())
        self.assertTrue(
            (self.destination / ".config/fish/conf.d/00-environment.fish").is_file()
        )
        self.assertTrue(
            (self.destination / ".config/fish/functions/linux/grd-rdp.fish").is_file()
        )
        self.assertEqual(
            (self.destination / ".config/fish/conf.d/apm.fish").read_text(),
            "# Installer-owned\n",
        )
