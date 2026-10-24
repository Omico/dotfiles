"""Render lifecycle scripts while keeping each test's data and config explicit."""

import json
import shutil
import subprocess
import unittest
from collections.abc import Mapping
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def render_script(source: Path, config: Path, data: Mapping[str, object]) -> str:
    chezmoi = shutil.which("chezmoi")
    if chezmoi is None:
        raise unittest.SkipTest("chezmoi is required")
    result = subprocess.run(
        [
            chezmoi,
            "--source",
            str(ROOT),
            "--config",
            str(config),
            "--override-data",
            json.dumps(data),
            "execute-template",
            "--file",
            str(source),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise AssertionError(result.stderr)
    return result.stdout
