"""Exercise the Zed apply helper in an isolated HOME."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APPLY_SCRIPT = ROOT / "app-settings/apply.fish"


class ZedTests(unittest.TestCase):
    def setUp(self):
        self.fish = shutil.which("fish")
        if not self.fish or not shutil.which("jq") or not shutil.which("iconv"):
            self.skipTest("fish, jq, and iconv are required")
        directory = tempfile.TemporaryDirectory(prefix="zed-settings-")
        self.addCleanup(directory.cleanup)
        self.home = Path(directory.name)
        self.source = self.home / ".local/share/chezmoi/app-settings/zed"
        self.source.mkdir(parents=True)
        self.shared = self.source / "settings.shared.json"
        self.shared.write_text('{"theme": "managed", "agent_servers": {"bad": 1}}')
        (self.source / "settings.ignored.json").write_text('["agent_servers"]')
        self.live = self.home / ".config/zed/settings.json"
        self.live.parent.mkdir(parents=True)
        self.live.write_text(
            '// Local settings\n{"theme": "live", "agent_servers": {"local": 1},}'
        )

    def run_apply(self):
        return subprocess.run(
            [
                str(self.fish),
                "--no-config",
                "-c",
                'source "$APPLY_SCRIPT"; __app_settings_apply_zed "$SETTINGS_SOURCE"',
            ],
            env={
                **os.environ,
                "HOME": str(self.home),
                "APPLY_SCRIPT": str(APPLY_SCRIPT),
                "SETTINGS_SOURCE": str(self.source),
            },
            capture_output=True,
            text=True,
            check=False,
        )

    def test_apply_preserves_local_integrations(self):
        result = self.run_apply()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(self.live.read_text()),
            {"theme": "managed", "agent_servers": {"local": 1}},
        )

    def test_invalid_input_preserves_both_files(self):
        self.live.write_text('{"broken":')
        shared_before = self.shared.read_bytes()
        live_before = self.live.read_bytes()
        result = self.run_apply()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.shared.read_bytes(), shared_before)
        self.assertEqual(self.live.read_bytes(), live_before)


if __name__ == "__main__":
    unittest.main()
