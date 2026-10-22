"""Verify native cleanup and Rime file ownership in isolated destinations."""

import json
import os
import shlex
import shutil
import subprocess
import tempfile
import tomllib
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
        shutil.copytree(ROOT / "macos", self.source / "macos")
        (self.source / ".chezmoiroot").write_text("home\n")
        self.config = self.root / "config/chezmoi.toml"
        self.config.parent.mkdir()
        self.config.write_text("")

    def run_chezmoi(self, *args, platform="darwin", codename="noble"):
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
                            "osRelease": {"id": "ubuntu", "ubuntuCodename": codename},
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

    def test_android_generated_completions_stay_local_on_both_platforms(self):
        target = self.write_target(
            ".config/fish/completions/android.fish", "# Locally generated\n"
        )
        for platform in ("darwin", "linux"):
            with self.subTest(platform=platform):
                self.run_chezmoi("apply", "--exclude=scripts", platform=platform)
                self.assertEqual(target.read_text(), "# Locally generated\n")
                self.assertTrue(
                    (
                        self.destination / ".local/libexec/android-fish-completions.py"
                    ).is_file()
                )

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
        existing_source = (
            self.source / "home/dot_config/fish/exact_functions/existing.fish"
        )
        existing_source.write_text("# Original source\n")
        starship_source = self.source / "home/dot_config/starship.toml"
        starship_template = starship_source.with_suffix(".toml.tmpl")
        starship_source.rename(starship_template)
        starship_template.write_text('format = "source"\n')
        self.run_chezmoi("apply", "--exclude=scripts")
        self.write_target(
            ".config/fish/functions/existing.fish", "# Captured local change\n"
        )
        self.write_target(".config/fish/functions/new.fish", "# Captured new file\n")
        self.write_target(".config/starship.toml", 'format = "local"\n')
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
        self.assertEqual(existing_source.read_text(), "# Captured local change\n")
        self.assertEqual(
            (existing_source.parent / "new.fish").read_text(), "# Captured new file\n"
        )
        self.assertEqual(starship_template.read_text(), 'format = "source"\n')
        self.assertFalse(starship_source.exists())
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

    @unittest.skipUnless(FISH, "fish is required")
    def test_package_templates_enforce_conditions_and_valid_names(self):
        scripts = {
            "run_onchange_before_20-darwin-formulae.fish.tmpl": "darwin",
            "run_onchange_after_30-darwin-apps.fish.tmpl": "darwin",
            "run_onchange_before_21-ubuntu-noble-apt.fish.tmpl": "noble",
        }
        for name, supported in scripts.items():
            source = self.source / "home" / name
            for platform in ("darwin", "linux", "windows"):
                with self.subTest(script=name, platform=platform):
                    rendered = self.run_chezmoi(
                        "execute-template", "--file", str(source), platform=platform
                    )
                    self.assertEqual(
                        bool(rendered.strip()),
                        supported == "noble" or platform == supported,
                    )
                    if rendered.strip():
                        result = subprocess.run(
                            [str(FISH), "--no-config", "--no-execute"],
                            input=rendered,
                            capture_output=True,
                            text=True,
                            check=False,
                        )
                        self.assertEqual(result.returncode, 0, result.stderr)
        apt_script = (
            self.source / "home/run_onchange_before_21-ubuntu-noble-apt.fish.tmpl"
        )
        for codename in ("jammy", ""):
            with self.subTest(codename=codename):
                self.assertFalse(
                    self.run_chezmoi(
                        "execute-template",
                        "--file",
                        str(apt_script),
                        platform="linux",
                        codename=codename,
                    ).strip()
                )
        manifest = self.source / "home/.chezmoidata/darwin.toml"
        original = manifest.read_text()
        manifest.write_text(original.replace('"aria2"', '"bad;package"'))
        result = subprocess.run(
            [
                str(CHEZMOI),
                "--source",
                str(self.source),
                "--config",
                str(self.config),
                "--override-data",
                '{"chezmoi":{"os":"darwin"}}',
                "execute-template",
                "--file",
                str(
                    self.source
                    / "home/run_onchange_before_20-darwin-formulae.fish.tmpl"
                ),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Invalid package name", result.stderr)
        manifest.write_text(original.replace('["aria2", "jq", "starship", "yq"]', "[]"))
        self.assertNotIn(
            "brew install",
            self.run_chezmoi(
                "execute-template",
                "--file",
                str(
                    self.source
                    / "home/run_onchange_before_20-darwin-formulae.fish.tmpl"
                ),
            ),
        )

    @unittest.skipUnless(FISH, "fish is required")
    def test_vscode_repository_is_configured_with_existing_code_and_retries(self):
        mock_bin = self.root / "repository-bin"
        mock_bin.mkdir()
        system = self.root / "system"
        system.mkdir()
        bodies = {
            "code": "exit 0\n",
            "curl": 'test "$CURL_FAIL" != 1 || exit 7\nprintf "mock-key\\n" >"$4"\n',
            "gpg": 'cp "$4" "$3"\n',
            "dpkg": "echo amd64\n",
            "sudo": """printf '%s\\n' "$*" >> "$MOCK_SYSTEM/calls"
case "$1" in
install)
    target="$MOCK_SYSTEM$5"
    mkdir -p "$(dirname "$target")"
    cp "$4" "$target";;
debconf-set-selections) cp "$2" "$MOCK_SYSTEM/code.seed";;
*) exit 91;;
esac
""",
        }
        for name, body in bodies.items():
            binary = mock_bin / name
            binary.write_text("#!/bin/sh\n" + body)
            binary.chmod(0o755)
        script = (
            self.source
            / "home/run_once_before_20-ubuntu-noble-vscode-repository.fish.tmpl"
        )
        args = [
            str(CHEZMOI),
            "--source",
            str(self.source),
            "--destination",
            str(self.destination),
            "--config",
            str(self.config),
            "--persistent-state",
            str(self.root / "state.boltdb"),
            "--override-data",
            '{"chezmoi":{"os":"linux","osRelease":{"ubuntuCodename":"noble"}}}',
            "apply",
            "--source-path",
            str(script),
        ]
        env = {
            **os.environ,
            "HOME": str(self.destination),
            "MOCK_SYSTEM": str(system),
            "PATH": str(mock_bin)
            + os.pathsep
            + str(Path(str(FISH)).parent)
            + ":/usr/bin:/bin",
        }
        result = subprocess.run(
            args,
            env={**env, "CURL_FAIL": "1"},
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((system / "calls").exists())
        result = subprocess.run(
            args,
            env={**env, "CURL_FAIL": "0"},
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        repository = (system / "etc/apt/sources.list.d/vscode.sources").read_text()
        self.assertIn("URIs: https://packages.microsoft.com/repos/code\n", repository)
        self.assertIn("Architectures: amd64\n", repository)
        self.assertEqual(
            (system / "usr/share/keyrings/microsoft.gpg").read_text(), "mock-key\n"
        )
        self.assertEqual(
            (system / "code.seed").read_text(),
            "code code/add-microsoft-repo boolean true\n",
        )
        calls = (system / "calls").read_text()
        result = subprocess.run(
            args, env=env, capture_output=True, text=True, check=False
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((system / "calls").read_text(), calls)

    @unittest.skipUnless(FISH, "fish is required")
    def test_package_list_changes_and_reverts_rerun_the_installer(self):
        log = self.root / "install-calls"
        mock_bin = self.root / "bin"
        mock_bin.mkdir()
        sudo = mock_bin / "sudo"
        sudo.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$INSTALL_CALLS"\n')
        sudo.chmod(0o755)
        script = self.source / "home/run_onchange_before_21-ubuntu-noble-apt.fish.tmpl"
        args = [
            str(CHEZMOI),
            "--source",
            str(self.source),
            "--destination",
            str(self.destination),
            "--config",
            str(self.config),
            "--persistent-state",
            str(self.root / "state.boltdb"),
            "--override-data",
            (
                '{"chezmoi":{"os":"linux","kernel":{"osrelease":"6.8.0"},'
                '"osRelease":{"id":"ubuntu","ubuntuCodename":"noble"}}}'
            ),
            "apply",
            "--source-path",
            str(script),
        ]
        env = {
            **os.environ,
            "HOME": str(self.destination),
            "PATH": str(mock_bin)
            + os.pathsep
            + str(Path(str(FISH)).parent)
            + os.pathsep
            + "/usr/bin:/bin",
            "INSTALL_CALLS": str(log),
        }

        def apply():
            result = subprocess.run(
                args, env=env, capture_output=True, text=True, check=False
            )
            self.assertEqual(result.returncode, 0, result.stderr)

        apply()
        first_calls = log.read_text()
        install = next(
            line for line in first_calls.splitlines() if line.startswith("apt install")
        )
        self.assertIn("fcitx5-rime", shlex.split(install))
        apply()
        self.assertEqual(log.read_text(), first_calls)
        manifest = self.source / "home/.chezmoidata/ubuntu.toml"
        original = manifest.read_text()
        manifest.write_text(original.replace('"zip",', '"zip",\n    "test-package",'))
        apply()
        self.assertIn("test-package", log.read_text())
        changed_calls = log.read_text()
        manifest.write_text(original)
        apply()
        self.assertEqual(log.read_text(), changed_calls + first_calls)
        current_calls = log.read_text()
        packages = tomllib.loads(original)["packages"]["ubuntu"]["noble"]["apt"]
        empty = original
        for package in packages:
            empty = empty.replace(f'    "{package}",\n', "")
        manifest.write_text(empty)
        apply()
        self.assertEqual(log.read_text(), current_calls)
        manifest.write_text(original)
        apply()
        self.assertEqual(log.read_text(), current_calls + first_calls)
