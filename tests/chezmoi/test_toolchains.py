"""Check shell toolchain boundaries using isolated homes and real archive formats."""

import io
import json
import os
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FUNCTIONS = ROOT / "home/dot_config/fish/exact_functions"
FISH = shutil.which("fish")


@unittest.skipUnless(FISH, "fish is required")
class ShellToolchainTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="shell-toolchain-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.binaries = self.root / "bin"
        self.binaries.mkdir()
        self.env = {
            **os.environ,
            "HOME": str(self.root),
            "PATH": str(self.binaries),
            "XDG_CONFIG_HOME": str(self.root / "config"),
        }

    def executable(self, name, body):
        path = self.binaries / name
        path.write_text(body)
        path.chmod(0o755)

    def run_fish(self, function, command, *, cwd=None):
        return subprocess.run(
            [
                str(FISH),
                "--no-config",
                "-c",
                f"source {shlex.quote(str(FUNCTIONS / function))}\n" + command,
            ],
            env=self.env,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_gradle_respects_directory_and_file_git_boundaries(self):
        self.executable("gradle", '#!/bin/sh\nprintf "GLOBAL %s\\n" "$*"\n')
        for command in ("dirname",):
            binary = shutil.which(command)
            assert binary
            (self.binaries / command).symlink_to(binary)
        outside = self.root / "gradlew"
        outside.write_text("#!/bin/sh\necho OUTSIDE\n")
        outside.chmod(0o755)
        for boundary in ("directory", "file"):
            repo = self.root / boundary
            nested = repo / "nested"
            nested.mkdir(parents=True)
            git = repo / ".git"
            if boundary == "file":
                git.write_text("gitdir: /unused\n")
            else:
                git.mkdir()
            result = self.run_fish(
                "gradle-or-gradlew.fish", "gradle-or-gradlew --version", cwd=nested
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "GLOBAL --version")
            wrapper = repo / "gradlew"
            wrapper.write_text('#!/bin/sh\nprintf "LOCAL %s\\n" "$*"\n')
            wrapper.chmod(0o755)
            result = self.run_fish(
                "gradle-or-gradlew.fish", "gradle-or-gradlew test", cwd=nested
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("LOCAL test", result.stdout)
            self.assertNotIn("OUTSIDE", result.stdout)

    def test_missing_jenv_returns_failure_without_exiting_the_shell(self):
        result = self.run_fish(
            "exact_darwin/update-jenv.fish",
            'update-jenv; set -l result $status; echo "SURVIVED=$result"',
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "SURVIVED=1")
        self.assertIn("jEnv not installed", result.stderr)

    def test_gitkraken_passes_literal_project_paths_without_executing_them(self):
        app = self.root / "GitKraken.app"
        binary = app / "Contents/MacOS/GitKraken"
        binary.parent.mkdir(parents=True)
        binary.write_text(
            f"#!{sys.executable}\n"
            "import json, os, sys\nfrom pathlib import Path\n"
            "(Path(os.environ['HOME']) / 'calls.json').write_text(json.dumps(sys.argv[1:]))\n"
        )
        binary.chmod(0o755)
        realpath = shutil.which("realpath")
        assert realpath
        (self.binaries / "realpath").symlink_to(realpath)
        self.executable("touch", '#!/bin/sh\necho executed > "$HOME/injected"\n')
        self.env["GITKRAKEN_APP_PATH"] = str(app)
        for name in (
            "project with spaces",
            "project; touch marker",
            "project(touch marker)",
        ):
            directory = self.root / name
            directory.mkdir()
            self.env["project_path"] = str(directory)
            result = self.run_fish(
                "exact_darwin/gitkraken.fish",
                'gitkraken "$project_path"; set -l result $status; wait; exit $result',
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((self.root / "injected").exists())
            self.assertEqual(
                json.loads((self.root / "calls.json").read_text()),
                ["-p", str(directory.resolve())],
            )

    @unittest.skipUnless(shutil.which("jq"), "jq is required")
    def test_flutter_installs_linux_wsl_and_macos_archives(self):
        for platform in ("linux", "wsl", "darwin"):
            with self.subTest(platform=platform):
                result = self.run_flutter(platform)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue((self.root / "flutter/bin/flutter").exists())
                self.assertEqual(
                    (self.root / "calls").read_text().splitlines(),
                    ["--disable-analytics", "--disable-analytics", "upgrade"],
                )

    @unittest.skipUnless(shutil.which("jq"), "jq is required")
    def test_flutter_reports_corrupt_archives(self):
        for platform in ("linux", "darwin"):
            with self.subTest(platform=platform):
                result = self.run_flutter(platform, corrupt=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Failed to extract Flutter archive", result.stderr)
                self.assertFalse((self.root / "calls").exists())

    def run_flutter(self, platform, *, corrupt=False):
        shutil.rmtree(self.root / "flutter", ignore_errors=True)
        (self.root / "calls").unlink(missing_ok=True)
        for command in ("jq", "tar", "xz", "unzip", "mktemp", "rm", "head"):
            binary = shutil.which(command)
            assert binary
            target = self.binaries / command
            if not target.exists():
                target.symlink_to(binary)
        self.executable("uname", "#!/bin/sh\necho arm64\n")
        archive = (
            "flutter_macos.zip" if platform == "darwin" else "flutter_linux.tar.xz"
        )
        (self.root / "manifest.json").write_text(
            json.dumps(
                {
                    "base_url": "https://example.invalid/flutter",
                    "releases": [
                        {
                            "archive": archive,
                            "version": "1.2.3",
                            "dart_sdk_arch": "arm64",
                            "channel": "stable",
                        }
                    ],
                }
            )
        )
        binary_body = b'#!/bin/sh\necho "$*" >> "$HOME/calls"\n'
        bundle = self.root / "bundle"
        if corrupt:
            bundle.write_bytes(b"not an archive")
        elif platform == "darwin":
            with zipfile.ZipFile(bundle, "w") as zipped:
                info = zipfile.ZipInfo("flutter/bin/flutter")
                info.external_attr = 0o100755 << 16
                zipped.writestr(info, binary_body)
        else:
            with tarfile.open(bundle, "w:xz") as tar:
                info = tarfile.TarInfo("flutter/bin/flutter")
                info.mode = 0o755
                info.size = len(binary_body)
                tar.addfile(info, io.BytesIO(binary_body))
        self.executable(
            "curl",
            f"#!{sys.executable}\n"
            "import os, shutil, sys\nfrom pathlib import Path\n"
            "args = sys.argv[1:]\n"
            "source = 'manifest.json' if any(arg.endswith('.json') for arg in args) else 'bundle'\n"
            "shutil.copyfile(Path(os.environ['HOME']) / source, args[args.index('-o') + 1])\n",
        )
        return self.run_fish(
            "exact_unix/flutter-init.fish",
            f"set -g fish_platform {platform}\n"
            "function fish_add_path_if_exists; fish_add_path --path $argv; end\n"
            "flutter-init; or exit $status\n"
            "flutter-init",
        )


if __name__ == "__main__":
    unittest.main()
