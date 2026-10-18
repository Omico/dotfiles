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
from concurrent.futures import ThreadPoolExecutor
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

    def run_fish(self, function, command, *, cwd=None, input_text=None):
        return subprocess.run(
            [
                str(FISH),
                "--no-config",
                "-c",
                f"source {shlex.quote(str(FUNCTIONS / function))}\n" + command,
            ],
            env=self.env,
            cwd=cwd,
            input=input_text,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_brew_backup_stops_at_each_failed_step(self):
        self.executable(
            "brew", '#!/bin/sh\necho export >> "$HOME/calls"\nexit "$brew_status"\n'
        )
        self.executable(
            "chezmoi",
            '#!/bin/sh\necho "$3" >> "$HOME/calls"\n'
            'case "$3" in\n'
            'diff) exit "$diff_status";;\n'
            'add) exit "$add_status";;\n'
            'commit) exit "$commit_status";;\n'
            "*) exit 99;;\nesac\n",
        )
        for brew, diff, add, commit, expected, calls in (
            (7, 1, 0, 0, 7, ["export"]),
            (0, 128, 0, 0, 128, ["export", "diff"]),
            (0, 1, 9, 0, 9, ["export", "diff", "add"]),
            (0, 1, 0, 11, 11, ["export", "diff", "add", "commit"]),
            (0, 0, 0, 0, 0, ["export", "diff"]),
            (0, 1, 0, 0, 0, ["export", "diff", "add", "commit"]),
        ):
            with self.subTest(brew=brew, diff=diff, add=add, commit=commit):
                (self.root / "calls").unlink(missing_ok=True)
                self.env.update(
                    brew_status=str(brew),
                    diff_status=str(diff),
                    add_status=str(add),
                    commit_status=str(commit),
                )
                result = self.run_fish("exact_darwin/brew.fish", "brew-backup")
                self.assertEqual(result.returncode, expected, result.stderr)
                self.assertEqual((self.root / "calls").read_text().splitlines(), calls)

    def test_gi_stops_at_each_failed_step(self):
        prelude = (
            "function git\n"
            ' echo $argv[1] >> "$HOME/calls"\n'
            ' if test "$argv[1]" = "$failed_step"; return 7; end\n'
            ' if test "$argv[1]" = rev-parse; echo $initial_branch; end\n'
            " return 0\nend\n"
        )
        steps = ["init", "add", "commit", "rev-parse", "branch"]
        for failed_step in (*steps, ""):
            with self.subTest(failed_step=failed_step):
                (self.root / "calls").unlink(missing_ok=True)
                self.env.update(failed_step=failed_step, initial_branch="master")
                result = self.run_fish("gi.fish", prelude + "gi", cwd=self.root)
                self.assertEqual(
                    result.returncode, 7 if failed_step else 0, result.stderr
                )
                expected = (
                    steps[: steps.index(failed_step) + 1] if failed_step else steps
                )
                self.assertEqual(
                    (self.root / "calls").read_text().splitlines(), expected
                )
        (self.root / "calls").unlink()
        self.env["initial_branch"] = "main"
        result = self.run_fish("gi.fish", prelude + "gi", cwd=self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / "calls").read_text().splitlines(), steps[:-1])

    def test_gi_preserves_existing_git_when_removal_fails(self):
        (self.root / ".git").mkdir()
        result = self.run_fish(
            "gi.fish",
            "function rm; return 9; end\n"
            'function git; echo called > "$HOME/calls"; end\ngi',
            cwd=self.root,
            input_text="y\n",
        )
        self.assertEqual(result.returncode, 9, result.stderr)
        self.assertTrue((self.root / ".git").is_dir())
        self.assertFalse((self.root / "calls").exists())

    def test_gcl_preserves_scp_paths_and_host_overrides(self):
        self.executable(
            "git",
            f"#!{sys.executable}\n"
            "import json, os, sys\nfrom pathlib import Path\n"
            "(Path(os.environ['HOME']) / 'calls.json').write_text(json.dumps(sys.argv[1:]))\n",
        )
        for command in ("mkdir", "dirname", "seq"):
            binary = shutil.which(command)
            assert binary
            (self.binaries / command).symlink_to(binary)
        for remote in (
            "work.example:team/repo.git",
            "git@work.example:team/repo.git",
            "ssh://git@work.example:2222/team/repo.git",
            "https://work.example/team/repo.git",
        ):
            with self.subTest(remote=remote):
                self.env["remote"] = remote
                result = self.run_fish(
                    "gcl.fish",
                    'set -g gcl_remote_host_base_dirs work.example "$HOME/clone root"\n'
                    'gcl "$remote" --depth=1',
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(
                    json.loads((self.root / "calls.json").read_text()),
                    [
                        "clone",
                        "--depth=1",
                        remote,
                        str(self.root / "clone root/team/repo"),
                    ],
                )

    def test_keyring_commands_preserve_existing_files_and_report_real_state(self):
        keyring = self.root / ".local/share/keyrings/default.keyring"
        keyring.parent.mkdir(parents=True)
        prelude = (
            "function __ensure_user_dbus_env; return 0; end\n"
            "function __gnome_keyring_require_commands; return 0; end\n"
            "function __gnome_keyring_restart_secret_service; return 0; end\n"
            "function __gnome_keyring_kill_stuck_secret_tool; return 0; end\n"
            "function __gnome_keyring_login_keyring_locked; echo $mock_locked; end\n"
        )
        for command, locked, status in (
            ("gnome-keyring-restart", "false", 0),
            ("gnome-keyring-unlock", "false", 0),
            ("gnome-keyring-status", "false", 0),
            ("gnome-keyring-status --quiet", "false", 0),
            ("gnome-keyring-status --quiet", "true", 1),
            ("gnome-keyring-unlock", "true", 1),
        ):
            with self.subTest(command=command, locked=locked):
                keyring.write_bytes(b"existing keyring data")
                keyring.chmod(0o600)
                self.env["mock_locked"] = locked
                result = self.run_fish(
                    "exact_linux/gnome-keyring.fish", prelude + command
                )
                self.assertEqual(result.returncode, status, result.stderr)
                self.assertEqual(keyring.read_bytes(), b"existing keyring data")
                self.assertEqual(keyring.stat().st_mode & 0o777, 0o600)

    def test_rdp_setup_propagates_view_only_failure(self):
        prelude = (
            "function __ensure_user_dbus_env; return 0; end\n"
            "function __grd_rdp_require_commands; return 0; end\n"
            "function gnome-keyring-status; return 0; end\n"
            "function isatty; return 0; end\n"
            "function __grd_rdp_timeout\n"
            ' printf "%s\\n" "$argv" >> "$HOME/calls"\n'
            " if contains -- disable-view-only $argv; return $view_status; end\n"
            " return 0\nend\n"
        )
        for status in (7, 0):
            (self.root / "calls").unlink(missing_ok=True)
            self.env["view_status"] = str(status)
            result = self.run_fish(
                "exact_linux/grd-rdp.fish",
                prelude + "grd-rdp-set-credentials testuser",
                input_text="synthetic-password\n",
            )
            self.assertEqual(result.returncode, status, result.stderr)
            calls = (self.root / "calls").read_text()
            self.assertIn("disable-view-only", calls)
            self.assertEqual("systemctl --user restart" in calls, status == 0)
            self.assertEqual("grdctl status" in calls, status == 0)

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
                downloads = (self.root / "downloads").read_text().splitlines()
                self.assertEqual(len(downloads), 2)
                self.assertEqual(len(set(downloads)), 2)
                for destination in downloads:
                    self.assertEqual(Path(destination).parent, self.root / "temp files")
                self.assertEqual(list((self.root / "temp files").iterdir()), [])

    @unittest.skipUnless(shutil.which("jq"), "jq is required")
    def test_flutter_reports_corrupt_archives(self):
        for platform in ("linux", "darwin"):
            with self.subTest(platform=platform):
                result = self.run_flutter(platform, corrupt=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Failed to extract Flutter archive", result.stderr)
                self.assertFalse((self.root / "calls").exists())
                self.assertEqual(list((self.root / "temp files").iterdir()), [])

    @unittest.skipUnless(shutil.which("jq"), "jq is required")
    def test_flutter_parallel_installs_use_distinct_temporary_files(self):
        temporary = self.root / "shared temp files"
        workers = [ShellToolchainTests(), ShellToolchainTests()]
        for worker in workers:
            worker.setUp()
            self.addCleanup(worker.doCleanups)
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(worker.run_flutter, "darwin", temporary=temporary)
                for worker in workers
            ]
            for future in futures:
                result = future.result()
                self.assertEqual(result.returncode, 0, result.stderr)
        downloads = [
            path
            for worker in workers
            for path in (worker.root / "downloads").read_text().splitlines()
        ]
        self.assertEqual(len(downloads), 4)
        self.assertEqual(len(set(downloads)), 4)
        self.assertTrue(all(Path(path).parent == temporary for path in downloads))
        self.assertEqual(list(temporary.iterdir()), [])

    @unittest.skipUnless(shutil.which("jq"), "jq is required")
    def test_flutter_stops_when_temporary_file_creation_fails(self):
        for allocation, kind in ((1, "manifest"), (2, "archive")):
            with self.subTest(allocation=allocation):
                result = self.run_flutter("darwin", fail_tempfile=allocation)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(
                    f"Failed to create Flutter {kind} temporary file", result.stderr
                )
                downloads = self.root / "downloads"
                self.assertEqual(
                    len(downloads.read_text().splitlines())
                    if downloads.exists()
                    else 0,
                    allocation - 1,
                )
                self.assertFalse((self.root / "calls").exists())
                self.assertEqual(list((self.root / "temp files").iterdir()), [])

    def run_flutter(
        self, platform, *, corrupt=False, fail_tempfile=None, temporary=None
    ):
        shutil.rmtree(self.root / "flutter", ignore_errors=True)
        (self.root / "calls").unlink(missing_ok=True)
        (self.root / "downloads").unlink(missing_ok=True)
        (self.root / "allocations").unlink(missing_ok=True)
        temporary = temporary or self.root / "temp files"
        temporary.mkdir(exist_ok=True)
        self.env["TMPDIR"] = str(temporary)
        for command in ("jq", "tar", "xz", "unzip", "mktemp", "rm", "head"):
            binary = shutil.which(command)
            assert binary
            target = self.binaries / command
            if not target.exists():
                target.symlink_to(binary)
        if fail_tempfile is not None:
            (self.binaries / "mktemp").unlink()
            self.executable(
                "mktemp",
                f"#!{sys.executable}\n"
                "import os, sys\nfrom pathlib import Path\n"
                "counter = Path(os.environ['HOME']) / 'allocations'\n"
                "count = int(counter.read_text()) + 1 if counter.exists() else 1\n"
                "counter.write_text(str(count))\n"
                f"if count == {fail_tempfile}: sys.exit(73)\n"
                f"os.execv({shutil.which('mktemp')!r}, ['mktemp', *sys.argv[1:]])\n",
            )
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
            "destination = args[args.index('-o') + 1]\n"
            "with (Path(os.environ['HOME']) / 'downloads').open('a') as log:\n"
            "    log.write(destination + '\\n')\n"
            "source = 'manifest.json' if any(arg.endswith('.json') for arg in args) else 'bundle'\n"
            "shutil.copyfile(Path(os.environ['HOME']) / source, destination)\n",
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
