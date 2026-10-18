"""Verify APM additions preserve configuration when a stage fails."""

import os
import shlex
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FISH = shutil.which("fish")


@unittest.skipUnless(FISH and shutil.which("yq"), "fish and yq are required")
class AddSkillTests(unittest.TestCase):
    def test_normalizes_root_and_nested_skill_urls(self):
        with tempfile.TemporaryDirectory(prefix="apm-normalize-") as directory:
            result = subprocess.run(
                [
                    str(FISH),
                    "--no-config",
                    "-c",
                    'source "$argv[1]"; __apm-normalize-skill-refs $argv[2..-1]',
                    str(ROOT / "home/dot_config/fish/exact_conf.d/99-apm.fish"),
                    "https://github.com/example/root-skill/blob/main/SKILL.md",
                    "https://github.com/example/repo/blob/main/skills/demo/SKILL.md",
                    "https://github.com/example/repo/blob/main/skills/demo/",
                    "github.com/example/repo/skills/demo",
                    "example/root-skill",
                ],
                env={**os.environ, "HOME": directory},
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                result.stdout.splitlines(),
                [
                    "example/root-skill",
                    "example/repo/skills/demo",
                    "example/repo/skills/demo",
                    "example/repo/skills/demo",
                    "example/root-skill",
                ],
            )

    def exercise(self, stage, global_source=False, existing=True):
        with tempfile.TemporaryDirectory(prefix="apm-add-test-") as directory:
            root = Path(directory)
            sources = root / "source/dot_apm"
            runtime = root / ".apm"
            sources.mkdir(parents=True)
            runtime.mkdir()
            for name in ("base", "external"):
                (sources / f"apm.{name}.yml").write_text("dependencies:\n  apm: []\n")
            (sources / "apm.environment").write_text("external\n")
            source = sources / ("apm.base.yml" if global_source else "apm.custom.yml")
            original = (
                b'# Keep this comment.\ndependencies:\n  apm: ["existing/package"]\n'
            )
            if existing:
                source.write_bytes(original)
                source.chmod(0o600)
                (runtime / "apm.yml").write_bytes(b"# Original runtime\n")
            failure = {
                "add": "__apm-add-to-source",
                "merge": "__apm-merge-source-config",
                "install": "__apm-run-global-apm",
                "link": "__apm-link-skills-to-agents",
            }.get(stage)
            script = f"""
source {shlex.quote(str(ROOT / "home/dot_config/fish/exact_conf.d/99-apm.fish"))}
source {shlex.quote(str(ROOT / "home/dot_config/fish/exact_functions/apm-add-skill.fish"))}
function chezmoi
    if test "$argv[1]" = source-path
        echo {shlex.quote(str(root / "source"))}
    else
        printf '%s\\n' $argv >"$HOME/capture"
    end
end
function __apm-run-global-apm; return 0; end
function __apm-link-skills-to-agents; return 0; end
"""
            if failure:
                script += f"""
function {failure}
    printf 'partial write\\n' >{shlex.quote(str(source))}
    printf 'partial runtime\\n' >"$__apm_home/apm.yml"
    return 7
end
"""
            script += (
                "apm-add-skill "
                + ("--global " if global_source else "")
                + "existing/package new/package\n"
            )
            result = subprocess.run(
                [str(FISH), "--no-config", "-c", script],
                env={**os.environ, "HOME": directory},
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 7 if failure else 0, result.stderr)
            if failure:
                self.assertEqual(source.exists(), existing)
                self.assertEqual((runtime / "apm.yml").exists(), existing)
                if existing:
                    self.assertEqual(source.read_bytes(), original)
                    self.assertEqual(source.stat().st_mode & 0o777, 0o600)
                    self.assertEqual(
                        (runtime / "apm.yml").read_bytes(), b"# Original runtime\n"
                    )
                self.assertFalse((root / "capture").exists())
            else:
                self.assertIn("new/package", source.read_text())
                self.assertIn("existing/package", source.read_text())
                self.assertEqual(
                    (runtime / source.name).read_bytes(), source.read_bytes()
                )
                self.assertTrue((root / "capture").exists())
            self.assertEqual(list(root.glob("apm-add.*")), [])

    def test_failures_restore_local_and_global_snapshots(self):
        for stage in ("add", "merge", "install", "link"):
            for global_source in (False, True):
                with self.subTest(stage=stage, global_source=global_source):
                    self.exercise(stage, global_source=global_source)

    def test_failure_removes_new_configuration(self):
        self.exercise("install", existing=False)

    def test_success_keeps_additions_and_captures_source(self):
        self.exercise("success")


if __name__ == "__main__":
    unittest.main()
