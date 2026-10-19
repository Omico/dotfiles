"""Verify rendered update scripts propagate failures to chezmoi."""

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
class UpdateTests(unittest.TestCase):
    def run_update(
        self,
        name,
        failed_command="",
        missing=(),
        *,
        bootstrap_rust=False,
        platform="darwin",
    ):
        with tempfile.TemporaryDirectory(prefix="chezmoi-update-") as directory:
            root = Path(directory)
            binaries = root / "bin"
            binaries.mkdir()
            for command in (
                "brew",
                "mas",
                "fnm",
                "rustup",
                "rustc",
                "snap",
                "sudo",
                "uv",
            ):
                if command in missing:
                    continue
                binary = binaries / command
                if bootstrap_rust and command == "rustc":
                    binary = root / "rustc-stub"
                binary.write_text(
                    "#!/bin/sh\n"
                    f'echo "{command} $*" >> "$HOME/calls"\n'
                    f'[ "{command} $*" != "$failed_command" ] || exit 7\n'
                    + (
                        '/bin/mkdir -p "$HOME/.cargo/bin"\n'
                        '/bin/cp "$HOME/rustc-stub" "$HOME/.cargo/bin/rustc"\n'
                        if bootstrap_rust and command == "rustup"
                        else ""
                    )
                    + ('echo "rustc 1.0.0"\n' if command == "rustc" else "")
                    + "exit 0\n"
                )
                binary.chmod(0o755)
            source = ROOT / "home" / name
            script = source.read_text()
            if source.suffix == ".tmpl":
                config = root / "chezmoi.toml"
                config.write_text("")
                render = subprocess.run(
                    [
                        str(CHEZMOI),
                        "--source",
                        str(ROOT),
                        "--config",
                        str(config),
                        "--override-data",
                        json.dumps(
                            {"chezmoi": {"os": platform, "osRelease": {"id": "ubuntu"}}}
                        ),
                        "execute-template",
                        "--file",
                        str(source),
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(render.returncode, 0, render.stderr)
                script = render.stdout
            prelude = ""
            if "homebrew" in name:
                prelude = (
                    "source "
                    + shlex.quote(
                        str(
                            ROOT
                            / "home/dot_config/fish/exact_functions/exact_darwin/brew.fish"
                        )
                    )
                    + "\n"
                )
            if "node" in name:
                prelude = "function fnm-upgrade-latest-lts; fnm upgrade; end\n"
            result = subprocess.run(
                [str(FISH), "--no-config", "-c", prelude + script],
                env={
                    **os.environ,
                    "HOME": directory,
                    "PATH": str(binaries),
                    "failed_command": failed_command,
                },
                capture_output=True,
                text=True,
                check=False,
            )
            calls = root / "calls"
            return result, calls.read_text().splitlines() if calls.exists() else []

    def test_python_setup_stops_at_each_failed_step(self):
        steps = [
            "uv python install 3.11",
            "uv python install 3.13 --default --preview-features python-install-default",
            "uv tool install --python 3.11 thefuck",
        ]
        for index, step in enumerate(steps):
            with self.subTest(step=step):
                result, calls = self.run_update(
                    "run_onchange_after_30-python.fish.tmpl", step
                )
                self.assertEqual(result.returncode, 7, result.stderr)
                self.assertEqual(calls, steps[: index + 1])
        result, calls = self.run_update("run_onchange_after_30-python.fish.tmpl")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, steps)

    def test_python_maintenance_stops_at_each_failed_step(self):
        steps = [
            "uv self update",
            "uv python upgrade",
            "uv tool upgrade --all",
        ]
        for index, step in enumerate(steps):
            with self.subTest(step=step):
                result, calls = self.run_update("run_after_90-python.fish.tmpl", step)
                self.assertEqual(result.returncode, 7, result.stderr)
                self.assertEqual(calls, steps[: index + 1])
        result, calls = self.run_update("run_after_90-python.fish.tmpl")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, steps)

    def test_python_maintenance_platform_scope(self):
        for platform in ("linux", "windows"):
            with self.subTest(platform=platform):
                result, calls = self.run_update(
                    "run_after_90-python.fish.tmpl", platform=platform
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(bool(calls), platform == "linux")

    def test_homebrew_stops_at_each_failed_step(self):
        steps = [
            "brew update",
            "brew upgrade",
            "brew cleanup",
            "brew autoremove",
            "mas upgrade",
        ]
        for index, step in enumerate(steps):
            with self.subTest(step=step):
                result, calls = self.run_update("run_after_90-homebrew.fish.tmpl", step)
                self.assertEqual(result.returncode, 7, result.stderr)
                self.assertEqual(calls, steps[: index + 1])
        result, calls = self.run_update(
            "run_after_90-homebrew.fish.tmpl", missing=("mas",)
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, steps[:-1])

    def test_rust_stops_on_install_update_and_version_failure(self):
        steps = ["rustup toolchain install stable", "rustup update", "rustc --version"]
        for index, step in enumerate(steps):
            with self.subTest(step=step):
                result, calls = self.run_update("run_after_90-rust.fish.tmpl", step)
                self.assertEqual(result.returncode, 7, result.stderr)
                self.assertEqual(calls, steps[: index + 1])
        result, _ = self.run_update("run_after_90-rust.fish.tmpl", missing=("rustc",))
        self.assertEqual(result.returncode, 1, result.stderr)

    def test_node_and_snap_propagate_failure_and_skip_absent_tools(self):
        for name, step, tool in (
            ("run_after_90-node.fish", "fnm upgrade", "fnm"),
            ("run_after_90-ubuntu-snap.fish.tmpl", "sudo snap refresh", "snap"),
        ):
            with self.subTest(script=name):
                result, _ = self.run_update(name, step)
                self.assertEqual(result.returncode, 7, result.stderr)
                result, calls = self.run_update(name, missing=(tool,))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(calls, [])

    def test_rust_bootstrap_activates_cargo_path_in_the_same_process(self):
        result, calls = self.run_update(
            "run_after_90-rust.fish.tmpl", bootstrap_rust=True
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            calls,
            ["rustup toolchain install stable", "rustup update", "rustc --version"],
        )

    def test_all_scripts_return_zero_on_success(self):
        for name in (
            "run_after_90-homebrew.fish.tmpl",
            "run_after_90-rust.fish.tmpl",
            "run_after_90-node.fish",
            "run_after_90-ubuntu-snap.fish.tmpl",
        ):
            with self.subTest(script=name):
                result, _ = self.run_update(name)
                self.assertEqual(result.returncode, 0, result.stderr)


@unittest.skipUnless(FISH, "fish is required")
class NodeUpgradeTests(unittest.TestCase):
    def run_node(self, failed_command="", *, corepack=True, pnpm=False):
        with tempfile.TemporaryDirectory(prefix="node-upgrade-") as directory:
            root = Path(directory)
            binaries = root / "bin"
            binaries.mkdir()
            corepack_stub = root / "corepack-stub"
            corepack_stub.write_text(
                '#!/bin/sh\necho "corepack $*" >> "$HOME/calls"\n'
                '[ "corepack $*" != "$failed_command" ] || exit 7\nexit 0\n'
            )
            corepack_stub.chmod(0o755)
            if corepack:
                shutil.copy2(corepack_stub, binaries / "corepack")
            if pnpm:
                (binaries / "pnpm").write_text("#!/bin/sh\nexit 0\n")
                (binaries / "pnpm").chmod(0o755)
            bodies = {
                "fnm": """case "$1" in
list) printf '* v24.0.0 default\\n* v22.0.0\\n';;
list-remote) echo v24.0.0;;
esac
""",
                "npm": '/bin/cp "$HOME/corepack-stub" "$HOME/bin/corepack"\n',
            }
            for name, body in bodies.items():
                binary = binaries / name
                binary.write_text(
                    f'#!/bin/sh\necho "{name} $*" >> "$HOME/calls"\n'
                    f'[ "{name} $*" != "$failed_command" ] || exit 7\n'
                    + body
                    + "exit 0\n"
                )
                binary.chmod(0o755)
            script = "\n".join(
                "source " + shlex.quote(str(ROOT / path))
                for path in (
                    "home/dot_config/fish/exact_functions/fnm-upgrade-latest-lts.fish",
                    "home/run_after_90-node.fish",
                )
            )
            result = subprocess.run(
                [str(FISH), "--no-config", "-c", script],
                env={
                    **os.environ,
                    "HOME": directory,
                    "PATH": str(binaries) + ":/usr/bin:/bin",
                    "failed_command": failed_command,
                },
                capture_output=True,
                text=True,
                check=False,
            )
            return result, (root / "calls").read_text().splitlines()

    def test_failures_stop_the_real_node_update(self):
        for command in (
            "fnm use v24.0.0",
            "fnm default v24.0.0",
            "fnm uninstall v22.0.0",
            "npm install -g corepack@latest",
            "corepack enable",
            "corepack install -g pnpm@latest",
        ):
            with self.subTest(command=command):
                result, calls = self.run_node(
                    command, corepack=not command.startswith("npm")
                )
                self.assertEqual(result.returncode, 7, result.stderr)
                self.assertEqual(calls[-1], command)

    def test_success_bootstraps_corepack_or_reuses_pnpm(self):
        result, calls = self.run_node(corepack=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("npm install -g corepack@latest", calls)
        self.assertEqual(calls[-1], "corepack install -g pnpm@latest")
        result, calls = self.run_node(pnpm=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("corepack enable", calls)


if __name__ == "__main__":
    unittest.main()
