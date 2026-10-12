"""Exercise APM terminal input and discovery links in isolated directories."""

import fcntl
import os
import pty
import select
import shlex
import shutil
import subprocess
import tempfile
import termios
import time
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[2] / "home/dot_config/fish/conf.d/99-apm.fish"
FISH = shutil.which("fish")


def claim_terminal():
    os.setsid()
    fcntl.ioctl(0, termios.TIOCSCTTY, 0)


@unittest.skipUnless(FISH, "fish is required")
class ApmInteractionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="apm-interaction-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.sources = self.root / "dot_apm"
        self.sources.mkdir()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        for name in ("base", "external", "internal"):
            (self.sources / f"apm.{name}.yml").write_text("dependencies:\n  apm: []\n")
        self.selector = self.sources / "apm.environment"

    def selection_script(self, failed_gh=False):
        if failed_gh:
            gh = self.bin / "gh"
            gh.write_text("#!/bin/sh\nexit 1\n")
            gh.chmod(0o755)
        # Only the mock bin is visible: an installed gh cannot mask its absence.
        return f"""
source {shlex.quote(str(SOURCE))}
function chezmoi
    echo {shlex.quote(str(self.root))}
end
set -gx PATH {shlex.quote(str(self.bin))}
set -l paths (__apm-require-source-paths); or exit 1
test (count $paths) -eq 3
"""

    def run_terminal(self, script, answers):
        master, slave = pty.openpty()
        try:
            with subprocess.Popen(
                [str(FISH), "--no-config", "-c", script],
                stdin=slave,
                stdout=slave,
                stderr=slave,
                # This standalone test runner starts no threads.
                preexec_fn=claim_terminal,  # noqa: PLW1509
            ) as process:
                output = b""
                sent = 0
                deadline = time.monotonic() + 10
                try:
                    while process.poll() is None:
                        if time.monotonic() >= deadline:
                            self.fail(f"Terminal timed out: {output!r}")
                        if select.select([master], [], [], 0.05)[0]:
                            output += os.read(master, 65536)
                        # Wait for Fish's line editor before sending each answer.
                        ready = not termios.tcgetattr(master)[3] & termios.ICANON
                        if (
                            sent < len(answers)
                            and output.count(b"Selection:") > sent
                            and ready
                        ):
                            os.write(master, answers[sent])
                            sent += 1
                    return process.returncode, output
                finally:
                    if process.poll() is None:
                        process.kill()
                        process.wait()
        finally:
            os.close(master)
            os.close(slave)

    def test_missing_gh_without_terminal_does_not_save(self):
        result = subprocess.run(
            [str(FISH), "--no-config", "-c", self.selection_script()],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"before running without terminal input", result.stderr)
        self.assertFalse(self.selector.exists())

    def test_manual_selection_without_gh(self):
        for answer, expected in ((b"1\r", "external"), (b"2\r", "internal")):
            with self.subTest(expected=expected):
                status, output = self.run_terminal(self.selection_script(), [answer])
                self.assertEqual(status, 0, output)
                self.assertEqual(self.selector.read_text(), expected + "\n")
                self.selector.unlink()

    def test_failed_gh_reprompts_after_invalid_selection(self):
        status, output = self.run_terminal(
            self.selection_script(failed_gh=True), [b"invalid\r", b"internal\r"]
        )
        self.assertEqual(status, 0, output)
        self.assertIn(b"Enter 1 (external) or 2 (internal).", output)
        self.assertEqual(self.selector.read_text(), "internal\n")

    def test_cancellation_does_not_save(self):
        for answer in (b"\x04", b"\x03"):
            with self.subTest(answer=answer):
                status, output = self.run_terminal(self.selection_script(), [answer])
                self.assertNotEqual(status, 0, output)
                self.assertFalse(self.selector.exists())

    def test_link_ownership_and_repeat_run(self):
        apm = self.root / "apm"
        skills = apm / ".agents/skills"
        agents = self.root / "agents"
        links = agents / "skills"
        skills.mkdir(parents=True)
        links.mkdir(parents=True)
        for name in ("new", "owned", "plugin", "broken"):
            (skills / name).mkdir()
        plugin = self.root / "plugin"
        plugin.mkdir()
        (links / "plugin").symlink_to(plugin)
        (links / "broken").symlink_to(self.root / "missing-plugin")
        (links / "owned").symlink_to(skills / "owned")
        (links / "stale").symlink_to(skills / "stale")
        # Redirect only the discovery root; never change the user's HOME.
        source = SOURCE.read_text().replace(
            'set -l agents_root "$HOME/.agents"',
            'set -l agents_root "$apm_test_agents"',
        )
        self.assertNotIn('set -l agents_root "$HOME/.agents"', source)
        script = (
            source
            + f"""
set -g __apm_home {shlex.quote(str(apm))}
set -g apm_test_agents {shlex.quote(str(agents))}
__apm-link-skills-to-agents
"""
        )
        for _ in range(2):
            result = subprocess.run(
                [str(FISH), "--no-config", "-c", script],
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((links / "plugin").readlink(), plugin)
            self.assertEqual(
                (links / "broken").readlink(), self.root / "missing-plugin"
            )
            for name in ("new", "owned"):
                self.assertEqual((links / name).readlink(), skills / name)
            self.assertFalse((links / "stale").is_symlink())
        (skills / "local").mkdir()
        (links / "local").mkdir()
        marker = links / "local/SKILL.md"
        marker.write_text("Local skill\n")
        result = subprocess.run(
            [str(FISH), "--no-config", "-c", script], capture_output=True, check=False
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(marker.read_text(), "Local skill\n")
        self.assertFalse((links / "local").is_symlink())


if __name__ == "__main__":
    unittest.main()
