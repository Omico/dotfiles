"""Verify Rime installation, retry behavior, and native file application."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from .support import render_script

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "home/run_once_before_30-rime-ice.fish.tmpl"
FISH = shutil.which("fish")
CHEZMOI = shutil.which("chezmoi")
RUBY = shutil.which("ruby")
pytestmark = pytest.mark.skipif(
    not (FISH and CHEZMOI), reason="fish and chezmoi required"
)


class RimeSetup:
    def __init__(self, root: Path, platform: str):
        self.root = root
        self.platform = platform
        self.source = root / "source"
        self.source.mkdir()
        self.destination = root / "destination"
        self.destination.mkdir()
        directory = (
            "Library/Rime" if platform == "darwin" else ".local/share/fcitx5/rime"
        )
        self.target = self.destination / directory
        self.custom = (
            self.source
            / directory.replace(".local/", "dot_local/")
            / "default.custom.yaml"
        )
        self.custom.parent.mkdir(parents=True)
        self.custom.write_text("custom\n")
        shutil.copy(SCRIPT, self.source)
        (root / "rime").mkdir()
        shutil.copy(ROOT / "rime/install.rb", root / "rime")
        self.config = root / "config.toml"
        self.config.write_text("")
        self.binaries = root / "bin"
        self.binaries.mkdir()
        commands = {
            "brew": '[ "$FAIL" != client ] || exit 7\n',
            "git": '[ "$FAIL" != clone ] || exit 7\n'
            '/bin/mkdir -p "$6"\n/usr/bin/touch "$6/installer.rb"\n',
            "ruby": '/bin/cat > "$CHOICES_FILE"\n'
            '[ "$FAIL" != installer ] || exit 7\n'
            '[ "$FAIL" != incomplete ] || exit 0\n'
            'if [ -d "$RIME_TARGET" ]; then /bin/mv "$RIME_TARGET" "$RIME_TARGET.old"; fi\n'
            '/bin/mkdir -p "$RIME_TARGET/cn_dicts"\n'
            'echo upstream > "$RIME_TARGET/rime_ice.schema.yaml"\n'
            'echo upstream > "$RIME_TARGET/cn_dicts/base.dict.yaml"\n'
            'echo upstream > "$RIME_TARGET/default.custom.yaml"\n',
        }
        for name, body in commands.items():
            binary = self.binaries / name
            binary.write_text(f'#!/bin/sh\necho {name} >> "$CALL_LOG"\n' + body)
            binary.chmod(0o755)

    def apply(self, failure=""):
        return subprocess.run(
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
                "--override-data",
                json.dumps({"chezmoi": {"os": self.platform}}),
                "apply",
            ],
            env={
                **os.environ,
                "HOME": str(self.destination),
                "PATH": f"{self.binaries}:{Path(str(FISH)).parent}:/usr/bin:/bin",
                "CALL_LOG": str(self.root / "calls"),
                "CHOICES_FILE": str(self.root / "choices"),
                "RIME_TARGET": str(self.target),
                "FAIL": failure,
            },
            capture_output=True,
            text=True,
            check=False,
        )

    def calls(self):
        log = self.root / "calls"
        return log.read_text().splitlines() if log.exists() else []


@pytest.fixture(params=["darwin", "linux"])
def rime(tmp_path: Path, request: pytest.FixtureRequest):
    return RimeSetup(tmp_path, request.param)


def test_bootstrap_applies_custom_files_and_runs_once(rime: RimeSetup):
    result = rime.apply()
    assert result.returncode == 0, result.stderr
    assert (rime.target / "default.custom.yaml").read_text() == "custom\n"
    assert (rime.target / "cn_dicts/base.dict.yaml").read_text() == "upstream\n"
    choices = ["1"] if rime.platform == "darwin" else ["3", "1"]
    assert (rime.root / "choices").read_text().splitlines() == choices

    local = rime.target / "user.yaml"
    local.write_text("local\n")
    rime.custom.write_text("changed\n")
    calls = rime.calls()
    result = rime.apply()
    assert result.returncode == 0, result.stderr
    assert (rime.target / "default.custom.yaml").read_text() == "changed\n"
    assert local.read_text() == "local\n"
    assert rime.calls() == calls


@pytest.mark.parametrize("failure", ["clone", "installer", "incomplete"])
def test_failed_setup_stops_file_application_and_retries(rime: RimeSetup, failure: str):
    assert rime.apply(failure).returncode != 0
    assert not (rime.target / "default.custom.yaml").exists()
    result = rime.apply()
    assert result.returncode == 0, result.stderr
    assert (rime.target / "default.custom.yaml").read_text() == "custom\n"
    assert rime.calls().count("git") == (2 if failure == "clone" else 1)


def test_existing_configuration_is_backed_up(rime: RimeSetup):
    rime.target.mkdir(parents=True)
    (rime.target / "rime_ice.schema.yaml").write_text("installed\n")
    local = rime.target / "user.yaml"
    local.write_text("local\n")
    result = rime.apply()
    assert result.returncode == 0, result.stderr
    backup = rime.target.with_name(rime.target.name + ".old")
    assert (backup / "user.yaml").read_text() == "local\n"
    assert rime.calls().count("ruby") == 1


@pytest.mark.parametrize("configured", [False, True])
def test_client_failure_retries_even_with_existing_schema(
    tmp_path: Path, configured: bool
):
    rime = RimeSetup(tmp_path, "darwin")
    if configured:
        rime.target.mkdir(parents=True)
        (rime.target / "rime_ice.schema.yaml").write_text("installed\n")
    assert rime.apply("client").returncode != 0
    assert rime.calls() == ["brew"]
    assert not (rime.target / "default.custom.yaml").exists()
    result = rime.apply()
    assert result.returncode == 0, result.stderr
    assert rime.calls().count("brew") == 2
    assert (rime.target / "default.custom.yaml").read_text() == "custom\n"


def test_unsupported_platform_has_no_script(tmp_path: Path):
    config = tmp_path / "config.toml"
    config.write_text("")
    assert render_script(SCRIPT, config, {"chezmoi": {"os": "windows"}}).strip() == ""


@pytest.mark.skipif(not RUBY, reason="ruby required")
@pytest.mark.parametrize("job", ["CloneConfigJob", "CopyCustomConfigJob"])
def test_upstream_command_failure_retries_despite_existing_schema(
    rime: RimeSetup, job: str
):
    rime.target.mkdir(parents=True)
    (rime.target / "rime_ice.schema.yaml").write_text("partial\n")
    checkout = rime.destination / "Git/Mark24Code/rime-auto-deploy"
    (checkout / "lib").mkdir(parents=True)
    (checkout / "lib/core.rb").write_text("module RimeDeploy; class Job; end; end\n")
    (checkout / "installer.rb").write_text(
        'require "./lib/core"\n'
        f"module RimeDeploy; class {job} < Job\n"
        '  def call; system("/bin/sh", "-c", \'[ "$FAIL" != partial ]\'); :next; end\n'
        "end; end\n"
        f"RimeDeploy::{job}.new.call\n"
    )
    (rime.binaries / "ruby").unlink()
    (rime.binaries / "ruby").symlink_to(str(RUBY))

    result = rime.apply("partial")
    assert result.returncode != 0
    assert "failed with exit" in result.stderr
    assert not (rime.target / "default.custom.yaml").exists()
    result = rime.apply()
    assert result.returncode == 0, result.stderr
    assert (rime.target / "default.custom.yaml").read_text() == "custom\n"
