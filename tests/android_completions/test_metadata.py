"""Verify help parsing, generation and Fish completion without Android."""

import os
import runpy
import shlex
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "scripts/android-fish-completions.py"

ROOT_HELP = """Usage: android [COMMAND]
  -h, --help  Show help
      --sdk=PARAM  Path to the Android SDK
Commands:
  skills  Manage skills with descriptions
          continued on another line
  describe  Describe a project
"""
GROUP_HELP = """Usage: android skills [COMMAND]
Options:
  -h, --help  Show help
      --sdk=PARAM  Path to the Android SDK
Commands:
  add  Install a skill
"""
LEAF_HELP = """Usage: android skills add [OPTIONS]
Options:
      --all  Install all skills
      --agent=PARAM  Select agents.
                     Defaults to all detected agents
      --project=PARAM  Path to a project root
  -o, --output=PARAM  Path to the output directory
      --screenshot=PARAM  A screenshot captured with `android screen capture
                          -a` to inspect
  -h, --help  Show help
android options:
      --sdk=PARAM  Path to the Android SDK
"""
DESCRIBE_HELP = """Usage: android describe [OPTIONS] <path>
Options:
  -h, --help  Show help
      --project_dir=PARAM
                   The project directory to describe
Positional Parameters:
  <path>  Path to a file
          relative to the working directory
"""


FISH = shutil.which("fish")


@unittest.skipUnless(FISH, "fish is required")
class GenerationTests(unittest.TestCase):
    def setUp(self):
        self.api = runpy.run_path(str(HELPER))
        self.temp = tempfile.TemporaryDirectory(prefix="android-completion-tests-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output = self.root / "completions/android.fish"
        self.broken = False
        self.calls = []
        self.context_help = {
            (): ROOT_HELP,
            ("skills",): GROUP_HELP,
            ("skills", "add"): LEAF_HELP,
            ("describe",): DESCRIBE_HELP,
        }
        self.patcher = patch.dict(
            self.api["write_completion"].__globals__, {"invoke": self.invoke}
        )
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def invoke(self, binary, args):
        self.calls.append(args)
        if args[-1] == "--help":
            if self.broken:
                return "Unknown help layout"
            return self.context_help[tuple(args[:-1])]
        self.fail(f"Unexpected functional command: {args}")

    def generate(self):
        self.api["write_completion"]("/fake/android", self.output)

    def run_fish(self, script, *, env=None):
        result = subprocess.run(
            [str(FISH), "--no-config", "-c", script],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        return result.stdout

    def test_multiline_help_and_option_examples_are_parsed(self):
        root = self.api["parse_help"](ROOT_HELP)
        self.assertEqual(
            root["commands"]["skills"],
            "Manage skills with descriptions continued on another line",
        )
        leaf = self.api["parse_help"](LEAF_HELP)
        self.assertEqual(
            leaf["options"]["--agent"]["description"],
            "Select agents. Defaults to all detected agents",
        )
        self.assertNotIn("-a", leaf["options"])
        self.assertEqual(
            leaf["options"]["--screenshot"]["description"],
            "A screenshot captured with `android screen capture -a` to inspect",
        )
        self.assertEqual(leaf["options"]["-h"], leaf["options"]["--help"])
        self.assertEqual(
            self.api["parse_help"](DESCRIBE_HELP)["options"]["--project_dir"][
                "path_kind"
            ],
            "directory",
        )

    def test_each_invocation_rebuilds_without_version_probes(self):
        self.generate()
        self.assertEqual(len(self.calls), 4)
        self.context_help[("skills", "add")] = LEAF_HELP.replace(
            "Install all skills", "Install every skill"
        )
        self.generate()
        self.assertIn("Install every skill", self.output.read_text())
        self.assertEqual(len(self.calls), 8)

    def test_option_groups_preserve_context_specific_definitions(self):
        self.context_help[("skills",)] = GROUP_HELP.replace(
            "Options:\n", "Options:\n      --all  List all skills\n"
        )
        self.generate()
        for query, expected in [
            ("android skills --all", "--all\tList all skills"),
            ("android skills add --all", "--all\tInstall all skills"),
        ]:
            with self.subTest(query=query):
                result = self.run_fish(
                    f"source {shlex.quote(str(self.output))}; complete -C {shlex.quote(query)}"
                )
                self.assertIn(expected, result)
        result = self.run_fish(
            f"source {shlex.quote(str(self.output))}; complete -C 'android describe --sdk'"
        )
        self.assertEqual(result, "")

    def test_failed_generation_preserves_previous_file(self):
        self.generate()
        original = self.output.read_bytes()
        self.broken = True
        with self.assertRaises(ValueError):
            self.generate()
        self.assertEqual(self.output.read_bytes(), original)

    def test_syntax_check_failure_preserves_file_and_cleans_temporary(self):
        self.generate()
        before = self.output.read_bytes()
        with (
            patch(
                "subprocess.run", side_effect=subprocess.CalledProcessError(1, "fish")
            ),
            self.assertRaises(subprocess.CalledProcessError),
        ):
            self.generate()
        self.assertEqual(self.output.read_bytes(), before)
        self.assertEqual(list(self.output.parent.iterdir()), [self.output])

    def test_completion_runs_no_android_or_python_processes(self):
        self.generate()
        binaries = self.root / "bin"
        binaries.mkdir()
        log = self.root / "calls"
        for name in ("android", "python3"):
            executable = binaries / name
            executable.write_text(
                f"#!/bin/sh\nprintf '%s\\n' {name} >> {shlex.quote(str(log))}\nexit 9\n"
            )
            executable.chmod(0o755)
        script = f"source {shlex.quote(str(self.output))}\n"
        for query in (
            "android ",
            "android skills add --",
            'android --sdk "SDK with spaces" skills add --ag',
        ):
            script += f"complete -C {shlex.quote(query)}\n"
        text = self.run_fish(
            script, env={**os.environ, "PATH": f"{binaries}:/usr/bin:/bin"}
        )
        self.assertIn(
            "skills\tManage skills with descriptions continued on another line",
            text,
        )
        self.assertIn("--agent\tSelect agents. Defaults to all detected agents", text)
        self.assertFalse(
            log.exists(), "Opening shells and completing must not run Android or Python"
        )

    def test_path_parameters_complete_files_and_directories(self):
        self.generate()
        (self.root / "candidate directory").mkdir()
        (self.root / "candidate-file.txt").write_text("")
        prefix = f"{self.root}/candidate"
        for arguments, kind in (
            ("--sdk ", "directory"),
            ("--sdk=", "directory"),
            ("describe --project_dir ", "directory"),
            ("describe ", "file"),
            ("skills add --project ", "directory"),
            ("skills add --agent ", "none"),
            ("skills add --screenshot ", "file"),
            ("skills add -o", "directory"),
            ("skills add -o ", "directory"),
            ("skills add --output=", "directory"),
            ("skills add --output ", "directory"),
        ):
            query = f"android {arguments}{prefix}"
            with self.subTest(query=query):
                result = self.run_fish(
                    f"source {shlex.quote(str(self.output))}; complete -C {shlex.quote(query)}"
                )
                if kind == "none":
                    self.assertEqual(result, "")
                    continue
                self.assertIn("candidate directory/", result)
                if kind == "file":
                    self.assertIn("candidate-file.txt", result)
                else:
                    self.assertNotIn("candidate-file.txt", result)

    def test_namespaces_and_directions_are_not_paths(self):
        self.assertEqual(
            self.api["path_kind"]("--dir=PARAM", "Direction to scroll"), ""
        )
        self.assertEqual(
            self.api["path_kind"](
                "--namespace=PARAM", "Namespace for Kotlin source files"
            ),
            "",
        )
