"""Check current upstream metadata contracts without downloading app archives."""

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
APPS = ROOT / "home/dot_config/exact_orchard/exact_apps"


@unittest.skipUnless(FISH and shutil.which("jq"), "fish and jq are required")
class ResolverTests(unittest.TestCase):
    def run_resolver(self, package, architecture, mock):
        with tempfile.TemporaryDirectory(prefix="orchard-resolver-") as directory:
            library = Path(directory) / "orchard.fish"
            library.write_text(
                (ROOT / "home/dot_local/bin/executable_orchard")
                .read_text()
                .split("# Main entry\n")[0]
            )
            return subprocess.run(
                [
                    str(FISH),
                    "--no-config",
                    "-c",
                    f"source {shlex.quote(str(library))}\n"
                    f"source {shlex.quote(str(APPS / (package + '.fish')))}\n"
                    + mock
                    + "\nfunction uname; echo $MOCK_ARCH; end\n"
                    "orchard_resolve_download_url_callback; or exit $status\n"
                    'printf "%s\\n" "$orchard_app_download_url"',
                ],
                env={**os.environ, "HOME": directory, "MOCK_ARCH": architecture},
                capture_output=True,
                text=True,
                check=False,
            )

    def test_opencode_selects_current_mac_asset_names(self):
        assets = {
            "assets": [
                {
                    "name": f"opencode-desktop-mac-{arch}.dmg",
                    "browser_download_url": f"https://example.invalid/{arch}.dmg",
                }
                for arch in ("arm64", "x64")
            ]
        }
        mock = (
            "function orchard_fetch_github_api\n"
            ' test "$argv[1]" = repos/anomalyco/opencode/releases/latest; or return 1\n'
            f" printf '%s' {shlex.quote(json.dumps(assets))}\nend\n"
        )
        for architecture, asset in (("arm64", "arm64"), ("x86_64", "x64")):
            with self.subTest(architecture=architecture):
                result = self.run_resolver("opencode-desktop", architecture, mock)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(
                    result.stdout.strip(), f"https://example.invalid/{asset}.dmg"
                )

    def test_zed_requests_the_supported_asset_parameter(self):
        mock = """
function curl
    string match -q '*asset=zed&stable=1&os=macos&arch=*' -- "$argv[-1]"; or return 22
    set -l expected_arch x86_64
    test "$MOCK_ARCH" = arm64; and set expected_arch aarch64
    string match -q "*arch=$expected_arch" -- "$argv[-1]"; or return 22
    printf '%s' '{"version":"test","url":"https://example.invalid/Zed.dmg"}'
end
"""
        for architecture in ("arm64", "x86_64"):
            with self.subTest(architecture=architecture):
                result = self.run_resolver("zed", architecture, mock)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(
                    result.stdout.strip(), "https://example.invalid/Zed.dmg"
                )


if __name__ == "__main__":
    unittest.main()
