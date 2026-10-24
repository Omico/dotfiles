"""Run application-specific lifecycle scripts without installed settings commands."""

import json
import os
import shlex
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FISH = shutil.which("fish")
CHEZMOI = shutil.which("chezmoi")


@unittest.skipUnless(FISH and CHEZMOI, "fish and chezmoi are required")
class AppSettingsTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="app settings ")
        self.addCleanup(directory.cleanup)
        self.home = Path(directory.name)
        self.repository = self.home / r"repository 'quotes' $dollars \backslash"
        self.source = self.repository / "app-settings"
        self.source.mkdir(parents=True)
        shutil.copy2(ROOT / "app-settings/apply.fish", self.source / "apply.fish")
        for app in ("vscode-based", "zed", "codex"):
            (self.source / app).mkdir()
        (self.source / "vscode-based/shared.json").write_text('{"managed": true}')
        (self.source / "zed/settings.shared.json").write_text('{"managed": true}')
        (self.source / "zed/settings.ignored.json").write_text('["local"]')
        self.config = self.home / "chezmoi.toml"
        self.config.write_text("")
        (self.home / "uv-stub").write_text(
            '#!/bin/sh\nprintf "%s\\n" "$@" > "$HOME/uv-args"\nexit "$UV_RUN_STATUS"\n'
        )
        (self.home / "uv-stub").chmod(0o755)

    def run_hook(self, app, *, platform="linux", run_status=0, install_status=0):
        render = subprocess.run(
            [
                str(CHEZMOI),
                "--source",
                str(ROOT),
                "--config",
                str(self.config),
                "--override-data",
                json.dumps(
                    {
                        "chezmoi": {
                            "os": platform,
                            "sourceDir": str(self.repository / "home"),
                        }
                    }
                ),
                "execute-template",
                "--file",
                str(ROOT / f"home/run_after_90-{app}-settings.fish.tmpl"),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(render.returncode, 0, render.stderr)
        prelude = "\n".join(
            "source " + shlex.quote(str(ROOT / path))
            for path in (
                "home/dot_config/fish/exact_conf.d/00-core-functions.fish",
                "home/dot_config/fish/exact_functions/exact_unix/uv.fish",
            )
        )
        prelude += """
function __uv_install
    echo install >>"$HOME/install-calls"
    test "$UV_INSTALL_STATUS" -eq 0; or return $UV_INSTALL_STATUS
    /bin/mkdir -p "$HOME/.local/bin"
    /bin/cp "$HOME/uv-stub" "$argv[1]"
end
"""
        return subprocess.run(
            [str(FISH), "--no-config", "-c", prelude + render.stdout],
            env={
                **os.environ,
                "HOME": str(self.home),
                "UV_RUN_STATUS": str(run_status),
                "UV_INSTALL_STATUS": str(install_status),
            },
            capture_output=True,
            text=True,
            check=False,
        )

    def test_json_hooks_apply_without_installed_settings_functions(self):
        for platform in ("linux", "darwin"):
            with self.subTest(platform=platform):
                result = self.run_hook("vscode", platform=platform)
                self.assertEqual(result.returncode, 0, result.stderr)
                prefix = (
                    self.home / "Library/Application Support"
                    if platform == "darwin"
                    else self.home / ".config"
                )
                for app in ("Code", "Cursor"):
                    live = prefix / app / "User/settings.json"
                    self.assertEqual(json.loads(live.read_text()), {"managed": True})
        result = self.run_hook("zed")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads((self.home / ".config/zed/settings.json").read_text()),
            {"managed": True},
        )

    def test_codex_installs_uv_once_and_forwards_helper_path(self):
        for _ in range(2):
            result = self.run_hook("codex")
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.home / "install-calls").read_text(), "install\n")
        self.assertEqual(
            (self.home / "uv-args").read_text().splitlines(),
            [
                "run",
                "--script",
                str(self.source / "codex/apply.py"),
            ],
        )

    def test_codex_install_and_helper_failures_propagate(self):
        result = self.run_hook("codex", install_status=7)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.home / "uv-args").exists())
        result = self.run_hook("codex", run_status=9)
        self.assertEqual(result.returncode, 9, result.stderr)

    def test_invalid_json_inputs_fail_without_creating_live_settings(self):
        for app, shared in (
            ("vscode", "vscode-based/shared.json"),
            ("zed", "zed/settings.shared.json"),
        ):
            with self.subTest(app=app):
                (self.source / shared).write_text("broken")
                result = self.run_hook(app)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(list(self.home.rglob("settings.json")), [])

    def test_missing_merge_helper_fails_and_unsupported_platform_skips(self):
        (self.source / "apply.fish").unlink()
        for app in ("vscode", "zed"):
            with self.subTest(app=app):
                self.assertNotEqual(self.run_hook(app).returncode, 0)
        for app in ("vscode", "zed", "codex"):
            with self.subTest(app=app, platform="windows"):
                result = self.run_hook(app, platform="windows")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "")
        self.assertFalse((self.home / "install-calls").exists())


if __name__ == "__main__":
    unittest.main()
