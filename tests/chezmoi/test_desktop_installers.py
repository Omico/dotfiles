"""Check fresh desktop installation paths without installing real applications."""

import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

from .support import ROOT, render_script

FISH = shutil.which("fish")
STUB = """import os, pathlib, sys
name = pathlib.Path(sys.argv[0]).name
args = sys.argv[1:]
with open(pathlib.Path.home() / 'calls', 'a') as log:
    log.write(name + ' ' + ' '.join(args) + '\\n')
if os.environ.get('FAIL_COMMAND') == name:
    sys.exit(7)
if name == 'dpkg':
    print(os.environ.get('ARCH', 'amd64'))
elif name == 'curl':
    pathlib.Path(args[args.index('-o') + 1]).write_text('exit 0\\n')
elif name == 'gpg':
    pathlib.Path(args[args.index('--output') + 1]).write_text('key')
elif name == 'sudo' and args[0] == 'install' and args[-1].endswith('.sources'):
    (pathlib.Path.home() / 'repository').write_text(pathlib.Path(args[-2]).read_text())
"""


@unittest.skipUnless(FISH and shutil.which("chezmoi"), "fish and chezmoi required")
class DesktopInstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="desktop-installers-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.config = self.root / "chezmoi.toml"
        self.config.write_text("")
        for name in ("curl", "sudo", "dpkg", "gpg", "sh"):
            target = self.bin / name
            target.write_text(f"#!{sys.executable}\n" + STUB)
            target.chmod(0o755)

    def run_script(self, name, *, platform="linux", codename="noble", **env):
        script = render_script(
            ROOT / "home" / name,
            self.config,
            {"chezmoi": {"os": platform, "osRelease": {"ubuntuCodename": codename}}},
        )
        result = subprocess.run(
            [str(FISH), "--no-config"],
            input=script,
            text=True,
            capture_output=True,
            check=False,
            env={
                **os.environ,
                "HOME": str(self.root),
                "PATH": f"{self.bin}:/usr/bin:/bin",
                **env,
            },
        )
        return result

    def calls(self):
        path = self.root / "calls"
        return path.read_text() if path.exists() else ""

    def test_linux_installers_scope_skip_and_failure(self):
        for app in ("chatgpt", "ghostty", "zed"):
            name = f"run_once_after_30-ubuntu-noble-{app}.fish.tmpl"
            for platform, codename in (("linux", "jammy"), ("darwin", "")):
                with self.subTest(app=app, platform=platform):
                    self.assertEqual(
                        self.run_script(
                            name, platform=platform, codename=codename
                        ).returncode,
                        0,
                    )
                    self.assertEqual(self.calls(), "")
            for command in (
                ("sudo",)
                if app == "ghostty"
                else ("curl", "sudo" if app == "chatgpt" else "sh")
            ):
                with self.subTest(app=app, failure=command):
                    result = self.run_script(name, FAIL_COMMAND=command)
                    self.assertEqual(result.returncode, 7, result.stderr)
                    (self.root / "calls").unlink()
            binary = self.bin / app
            binary.write_text("#!/bin/sh\nexit 0\n")
            binary.chmod(0o755)
            self.assertEqual(self.run_script(name).returncode, 0)
            self.assertEqual(self.calls(), "")
            binary.unlink()
            result = self.run_script(name)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(
                "snap install ghostty --classic"
                if app == "ghostty"
                else "curl -fsSL https://",
                self.calls(),
            )
            (self.root / "calls").unlink()

    def test_chatgpt_architecture_and_failed_download(self):
        name = "run_once_after_30-ubuntu-noble-chatgpt.fish.tmpl"
        for arch in ("amd64", "arm64"):
            self.assertEqual(self.run_script(name, ARCH=arch).returncode, 0)
            self.assertIn(f"chatgpt_{arch}.deb", self.calls())
        (self.root / "calls").unlink()
        self.assertEqual(self.run_script(name, ARCH="riscv64").returncode, 1)
        self.assertNotIn("curl", self.calls())
        (self.root / "calls").unlink()
        self.assertEqual(self.run_script(name, FAIL_COMMAND="curl").returncode, 7)
        self.assertNotIn("sudo", self.calls())

    def test_cursor_repository_is_signed_and_installed_before_apt(self):
        name = "run_once_before_20-ubuntu-noble-cursor-repository.fish.tmpl"
        self.assertEqual(self.run_script(name).returncode, 0)
        repository = (self.root / "repository").read_text()
        self.assertIn("URIs: https://downloads.cursor.com/aptrepo\n", repository)
        self.assertIn("Signed-By: /usr/share/keyrings/cursor.gpg\n", repository)
        self.assertIn("Architectures: amd64\n", repository)
        (self.root / "calls").unlink()
        self.assertEqual(self.run_script(name, FAIL_COMMAND="curl").returncode, 7)
        self.assertNotIn("sudo", self.calls())
        packages = tomllib.loads((ROOT / "home/.chezmoidata/ubuntu.toml").read_text())
        self.assertIn("cursor", packages["packages"]["ubuntu"]["noble"]["apt"])

    def test_macos_bootstrap_installs_editors_and_fnm(self):
        packages = tomllib.loads((ROOT / "home/.chezmoidata/darwin.toml").read_text())
        data = packages["packages"]["darwin"]
        self.assertIn("fnm", data["bootstrap_formulae"])
        self.assertTrue(
            {"chatgpt", "cursor", "ghostty", "zed"}.issubset(data["orchard"])
        )
        for app in data["orchard"]:
            self.assertTrue(
                (
                    ROOT / f"home/dot_config/exact_orchard/exact_apps/{app}.fish"
                ).is_file()
            )
