"""Check macOS lifecycle scripts without changing host settings, PAM, or Terminal."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHEZMOI = shutil.which("chezmoi")
FISH = shutil.which("fish")
SCRIPTS = {
    "touch-id": "run_onchange_after_20-darwin-touch-id.fish.tmpl",
    "preferences": "run_onchange_after_30-darwin-preferences.fish.tmpl",
    "terminal": "run_onchange_after_30-darwin-terminal.fish.tmpl",
}
PREFERENCES = [
    "com.apple.finder QuitMenuItem -bool true",
    "com.apple.finder AppleShowAllFiles -bool true",
    "NSGlobalDomain AppleShowAllExtensions -bool true",
    "com.apple.finder ShowStatusBar -bool true",
    "com.apple.finder ShowPathbar -bool true",
    "com.apple.finder _FXSortFoldersFirst -bool true",
    "com.apple.finder FXDefaultSearchScope -string SCcf",
    "com.apple.finder FXEnableExtensionChangeWarning -bool false",
    "com.apple.desktopservices DSDontWriteNetworkStores -bool true",
    "com.apple.desktopservices DSDontWriteUSBStores -bool true",
    "com.apple.dock tilesize -int 48",
    "com.apple.dock autohide -bool true",
    "com.apple.dock show-recents -bool false",
    "com.apple.SoftwareUpdate AutomaticCheckEnabled -bool true",
    "com.apple.commerce AutoUpdate -bool true",
    "-g com.apple.swipescrolldirection -bool false",
    "-g com.apple.mouse.linear 1",
    "-g com.apple.mouse.scaling 1",
]


@unittest.skipUnless(CHEZMOI and FISH, "chezmoi and fish are required")
class MacosTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="macos-setup-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source with 'quotes' and $dollars"
        self.home_source = self.source / "home"
        self.home_source.mkdir(parents=True)
        self.destination = self.root / "destination"
        self.destination.mkdir()
        self.pam = self.root / "pam"
        self.pam.mkdir()
        (self.pam / "sudo_local.template").write_text(
            "# Local sudo rules\n#auth       sufficient     pam_tid.so\n"
        )
        for name in SCRIPTS.values():
            script = (ROOT / "home" / name).read_text()
            (self.home_source / name).write_text(
                script.replace("/etc/pam.d", str(self.pam))
            )
        templates = self.home_source / ".chezmoitemplates"
        templates.mkdir()
        shutil.copy(ROOT / "home/.chezmoitemplates/installer-workdir.fish", templates)
        shutil.copytree(ROOT / "macos", self.source / "macos")
        (self.source / ".chezmoiroot").write_text("home\n")
        self.config = self.root / "config.toml"
        self.config.write_text("")
        self.binaries = self.root / "bin"
        self.binaries.mkdir()
        (self.binaries / "fish").symlink_to(str(FISH))
        for name in ("mktemp", "rm", "cat"):
            binary = shutil.which(name)
            assert binary
            (self.binaries / name).symlink_to(binary)
        for name in (
            "id",
            "launchctl",
            "defaults",
            "osascript",
            "sudo",
            "sysctl",
            "pgrep",
            "pkill",
        ):
            binary = self.binaries / name
            binary.write_text(
                f"#!{sys.executable}\n"
                "import json, os, shutil, sys\nfrom pathlib import Path\n"
                "name = Path(sys.argv[0]).name\nargs = sys.argv[1:]\n"
                "with (Path(os.environ['HOME']) / 'calls').open('a') as log:\n"
                "    log.write(json.dumps([name, *args]) + '\\n')\n"
                "if os.environ.get('FAIL_STEP') in (name, ' '.join([name, *args])):\n"
                "    sys.exit(int(os.environ.get('FAIL_CODE', '7')))\n"
                "if name == 'id': print('501')\n"
                "elif name in ('pgrep', 'pkill'):\n"
                "    assert args == ['-u', '501', '-x', 'Dock']\n"
                "    if name == 'pgrep': sys.exit(0 if os.environ['GUI_ACTIVE'] == '1' else 1)\n"
                "elif name == 'sysctl':\n"
                "    assert args == ['-n', 'kern.hv_vmm_present']\n"
                "    print(os.environ.get('VMM_PRESENT', '0'))\n"
                "elif name == 'launchctl': sys.exit(0 if os.environ['GUI_ACTIVE'] == '1' else 1)\n"
                "elif name == 'osascript':\n"
                "    if not all(Path(arg).is_file() for arg in args): sys.exit(91)\n"
                "elif name == 'sudo':\n"
                "    assert args[:8] == ['install', '-S', '-o', 'root', '-g', 'wheel', '-m', '0644']\n"
                "    shutil.copyfile(args[-2], args[-1])\n"
            )
            binary.chmod(0o755)
        self.work = self.root / "temporary files"
        self.work.mkdir()
        self.env = {
            **os.environ,
            "HOME": str(self.destination),
            "PATH": str(self.binaries),
            "XDG_CONFIG_HOME": str(self.destination / ".config"),
            "TMPDIR": str(self.work),
            "GUI_ACTIVE": "1",
            "FAIL_STEP": "",
        }

    def chezmoi(self, *args, platform="darwin"):
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
                str(self.root / "state.db"),
                "--cache",
                str(self.root / "cache"),
                "--override-data",
                json.dumps({"chezmoi": {"os": platform}}),
                *args,
            ],
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )

    def run_setup(self, name):
        rendered = self.chezmoi(
            "execute-template", "--file", str(self.home_source / SCRIPTS[name])
        )
        self.assertEqual(rendered.returncode, 0, rendered.stderr)
        return subprocess.run(
            [str(FISH), "--no-config"],
            input=rendered.stdout,
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )

    def calls(self):
        log = self.destination / "calls"
        return (
            [json.loads(line) for line in log.read_text().splitlines()]
            if log.exists()
            else []
        )

    def clear_calls(self):
        (self.destination / "calls").unlink(missing_ok=True)

    def test_preferences_preserve_all_values_and_stop_on_each_failure(self):
        expected = ["defaults write " + value for value in PREFERENCES]
        for index, failed in enumerate([*expected, ""]):
            with self.subTest(failed=failed):
                self.clear_calls()
                self.env["FAIL_STEP"] = failed
                result = self.run_setup("preferences")
                self.assertEqual(result.returncode, 7 if failed else 0, result.stderr)
                calls = [
                    " ".join(call) for call in self.calls() if call[0] == "defaults"
                ]
                self.assertEqual(calls, expected[: index + 1] if failed else expected)

    def test_preferences_can_run_without_gui_but_do_not_ignore_helper_failure(self):
        self.env["GUI_ACTIVE"] = "0"
        result = self.run_setup("preferences")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(any(call[0] == "osascript" for call in self.calls()))
        self.assertFalse(any(call[0] == "pkill" for call in self.calls()))
        self.clear_calls()
        self.env.update(GUI_ACTIVE="1", FAIL_STEP="osascript")
        result = self.run_setup("preferences")
        self.assertEqual(result.returncode, 7, result.stderr)
        self.assertFalse(any(call[0] == "defaults" for call in self.calls()))

    def test_virtual_machine_disables_dock_autohide(self):
        self.env["VMM_PRESENT"] = "1"
        result = self.run_setup("preferences")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(
            ["defaults", "write", "com.apple.dock", "autohide", "-bool", "false"],
            self.calls(),
        )

    def test_vm_detection_failure_does_not_write_dock_preferences(self):
        self.env["FAIL_STEP"] = "sysctl"
        result = self.run_setup("preferences")
        self.assertEqual(result.returncode, 7, result.stderr)
        self.assertFalse(any("com.apple.dock" in call for call in self.calls()))

    def test_dock_restarts_after_preferences_and_propagates_failure(self):
        for failed in ("", "pkill"):
            with self.subTest(failed=failed):
                self.clear_calls()
                self.env["FAIL_STEP"] = failed
                result = self.run_setup("preferences")
                self.assertEqual(result.returncode, 7 if failed else 0, result.stderr)
                calls = self.calls()
                restart = calls.index(["pkill", "-u", "501", "-x", "Dock"])
                dock_write = calls.index(
                    [
                        "defaults",
                        "write",
                        "com.apple.dock",
                        "show-recents",
                        "-bool",
                        "false",
                    ]
                )
                self.assertGreater(restart, dock_write)

    def test_dock_detection_failure_stops_setup_and_retries_on_apply(self):
        self.env.update(FAIL_STEP="pgrep", FAIL_CODE="3")
        args = (
            "apply",
            "--source-path",
            str(self.home_source / SCRIPTS["preferences"]),
        )
        result = self.chezmoi(*args)
        self.assertNotEqual(result.returncode, 0, result.stderr)
        self.assertFalse(any(call[0] == "pkill" for call in self.calls()))
        self.assertFalse(
            any("com.apple.SoftwareUpdate" in call for call in self.calls())
        )
        self.clear_calls()
        self.env["FAIL_STEP"] = ""
        result = self.chezmoi(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(["pkill", "-u", "501", "-x", "Dock"], self.calls())

    def test_fresh_apply_disables_natural_scrolling_and_skips_unchanged_setup(self):
        args = (
            "apply",
            "--source-path",
            str(self.home_source / SCRIPTS["preferences"]),
        )
        result = self.chezmoi(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(
            [
                "defaults",
                "write",
                "-g",
                "com.apple.swipescrolldirection",
                "-bool",
                "false",
            ],
            self.calls(),
        )
        self.clear_calls()
        result = self.chezmoi(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls(), [])

    def test_touch_id_preserves_existing_bytes_and_is_idempotent(self):
        target = self.pam / "sudo_local"
        for existing in (
            None,
            b"",
            b"# Custom rules\naccount required pam_permit.so\n# no final newline",
        ):
            with self.subTest(existing=existing):
                self.clear_calls()
                target.unlink(missing_ok=True)
                if existing is not None:
                    target.write_bytes(existing)
                original = (
                    existing
                    if existing is not None
                    else (self.pam / "sudo_local.template").read_bytes()
                )
                result = self.run_setup("touch-id")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(
                    target.read_bytes(),
                    b"auth       sufficient     pam_tid.so\n" + original,
                )
                self.assertEqual(list(self.work.iterdir()), [])
                self.clear_calls()
                result = self.run_setup("touch-id")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.calls(), [])

    def test_touch_id_does_not_bypass_custom_authentication_rules(self):
        target = self.pam / "sudo_local"
        for rule in (
            b"auth required pam_smartcard.so no_ignore\n",
            b"auth requisite pam_deny.so\n",
            b"auth include custom-policy\n",
            b"auth optional custom.so\n",
            b"auth required pam_tid.so\n",
            b"\tauth\trequired\tpam_smartcard.so no_ignore\n",
        ):
            with self.subTest(rule=rule):
                self.clear_calls()
                target.write_bytes(rule)
                result = self.run_setup("touch-id")
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn("custom authentication rules", result.stderr)
                self.assertEqual(target.read_bytes(), rule)
                self.assertEqual(self.calls(), [])
                self.assertEqual(list(self.work.iterdir()), [])

    def test_custom_authentication_failure_retries_after_manual_configuration(self):
        target = self.pam / "sudo_local"
        rule = b"auth required pam_smartcard.so no_ignore\n"
        target.write_bytes(rule)
        args = ("apply", "--source-path", str(self.home_source / SCRIPTS["touch-id"]))
        result = self.chezmoi(*args)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(target.read_bytes(), rule)
        configured = rule + b"auth sufficient pam_tid.so\n"
        target.write_bytes(configured)
        result = self.chezmoi(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(target.read_bytes(), configured)
        self.assertEqual(self.calls(), [])

    def test_touch_id_missing_input_and_install_failure_leave_original_unchanged(self):
        (self.pam / "sudo_local.template").unlink()
        result = self.run_setup("touch-id")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.calls(), [])
        target = self.pam / "sudo_local"
        target.write_bytes(b"# Preserve me\n")
        self.env["FAIL_STEP"] = "sudo"
        result = self.run_setup("touch-id")
        self.assertEqual(result.returncode, 7, result.stderr)
        self.assertEqual(target.read_bytes(), b"# Preserve me\n")
        self.assertEqual(list(self.work.iterdir()), [])

    def test_failed_gui_setup_retries_and_resource_changes_trigger_only_its_consumer(
        self,
    ):
        self.env["GUI_ACTIVE"] = "0"
        result = self.chezmoi("apply")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires a graphical login", result.stderr)
        self.clear_calls()
        self.env["GUI_ACTIVE"] = "1"
        result = self.chezmoi("apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            [call[0] for call in self.calls()], ["id", "launchctl", "osascript"]
        )
        self.clear_calls()
        result = self.chezmoi("apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls(), [])
        for resource, consumer in (
            ("My.terminal", "terminal-theme.applescript"),
            ("terminal-theme.applescript", "terminal-theme.applescript"),
            ("close-system-settings.applescript", "close-system-settings.applescript"),
        ):
            with self.subTest(resource=resource):
                self.clear_calls()
                path = self.source / "macos" / resource
                path.write_bytes(path.read_bytes() + b"\n")
                result = self.chezmoi("apply")
                self.assertEqual(result.returncode, 0, result.stderr)
                calls = [call for call in self.calls() if call[0] == "osascript"]
                self.assertEqual(len(calls), 1)
                self.assertEqual(Path(calls[0][1]).name, consumer)

    def test_osascript_failure_retries_without_recording_success(self):
        self.env["FAIL_STEP"] = "osascript"
        args = ("apply", "--source-path", str(self.home_source / SCRIPTS["terminal"]))
        result = self.chezmoi(*args)
        self.assertNotEqual(result.returncode, 0)
        self.clear_calls()
        self.env["FAIL_STEP"] = ""
        result = self.chezmoi(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls()[-1][0], "osascript")

    def test_non_macos_templates_are_empty_and_resources_stay_in_source(self):
        for platform in ("linux", "windows"):
            with self.subTest(platform=platform):
                result = self.chezmoi("apply", platform=platform)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.calls(), [])
                self.assertFalse((self.destination / "macos").exists())
                self.assertFalse((self.destination / ".local/share/dotfiles").exists())
