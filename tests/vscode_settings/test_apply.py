from __future__ import annotations

import codecs
import json
import os
import pathlib
import shutil
import stat
import subprocess
import tempfile
import textwrap
import unittest
from collections.abc import Mapping

ROOT = pathlib.Path(__file__).resolve().parents[2]
APPLY_FUNCTION = (
    ROOT / "home/dot_config/fish/functions/unix/vscode-settings-apply.fish"
)


class ApplyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fish = shutil.which("fish")
        cls.iconv = shutil.which("iconv")
        cls.jq = shutil.which("jq")
        cls.cat = shutil.which("cat")
        cls.cmp = shutil.which("cmp")
        cls.mv = shutil.which("mv")
        if any(
            tool is None
            for tool in (cls.fish, cls.iconv, cls.jq, cls.cat, cls.cmp, cls.mv)
        ):
            raise unittest.SkipTest("fish, iconv, jq, cat, cmp, and mv are required")

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(
            prefix="vscode-settings-apply-tests."
        )
        self.addCleanup(self.temp_dir.cleanup)
        self.home = pathlib.Path(self.temp_dir.name)
        self.source_dir = self.home / ".config/vscode-settings"
        self.code_live = self.home / ".config/Code/User/settings.json"
        self.cursor_live = self.home / ".config/Cursor/User/settings.json"
        self.source_dir.mkdir(parents=True)
        self.code_live.parent.mkdir(parents=True)
        self.cursor_live.parent.mkdir(parents=True)

    def run_apply(
        self, extra_env: Mapping[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update(
            {
                "HOME": str(self.home),
                "APPLY_FUNCTION": str(APPLY_FUNCTION),
            }
        )
        if extra_env is not None:
            env.update(extra_env)

        return subprocess.run(
            [
                self.fish,
                "--no-config",
                "-c",
                "set -g fish_platform linux; source $APPLY_FUNCTION; "
                "vscode-settings-apply",
            ],
            cwd=ROOT,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )

    def assert_apply_status(
        self, expected: int, result: subprocess.CompletedProcess[str]
    ) -> None:
        self.assertEqual(
            result.returncode,
            expected,
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )

    @staticmethod
    def read_json(path: pathlib.Path) -> dict[str, object]:
        with path.open(encoding="utf-8") as settings_file:
            return json.load(settings_file)

    def test_shallow_merge_optional_layer_jsonc_and_idempotency(self) -> None:
        (self.source_dir / "shared.json").write_text(
            textwrap.dedent(
                """
                {
                  "objectSetting": {"fromShared": true},
                  "ignoredSetting": "managed",
                  "codeIgnoredSetting": "managed",
                  "managedFalse": false,
                  "managedNull": null,
                  "managedLargeInteger": 9007199254740993,
                  "managedMergeKey": {"<<": {"nested": true}, "keep": 2}
                }
                """
            ).lstrip()
        )
        (self.source_dir / "cursor.json").write_text(
            '{\n  "objectSetting": {"fromCursor": true}\n}\n'
        )
        (self.source_dir / "ignored.json").write_text('["ignoredSetting"]\n')
        (self.source_dir / "code.ignored.json").write_text(
            '["codeIgnoredSetting"]\n'
        )

        code_jsonc = textwrap.dedent(
            r'''
            {
              // Code live settings are valid JSONC.
              "objectSetting": {"stale": true},
              "ignoredSetting": "code-live",
              "codeIgnoredSetting": "code-live",
              "liveOnly": "code",
              "url": "https://example.com/a//b",
              "literal": "/* not a comment */",
              "escaped": "quote: \" // still a string",
              "commaLiteral": ",}",
              "managedFalse": true,
              "managedNull": "stale",
              "liveLargeInteger": 9007199254740993,
              "liveMergeKey": {"<<": {"nested": true}, "keep": 2},
            }
            '''
        ).lstrip()
        self.code_live.write_bytes(
            codecs.BOM_UTF8 + code_jsonc.replace("\n", "\r\n").encode()
        )
        self.cursor_live.write_text(
            textwrap.dedent(
                """
                {
                  "objectSetting": {"stale": true}, /* Cursor comment. */
                  "ignoredSetting": "cursor-live",
                  "liveOnly": "cursor",
                  "managedFalse": true,
                  "managedNull": "stale",
                }
                """
            ).lstrip()
        )
        code_mode_before = stat.S_IMODE(self.code_live.stat().st_mode)
        cursor_mode_before = stat.S_IMODE(self.cursor_live.stat().st_mode)

        first_result = self.run_apply()

        self.assert_apply_status(0, first_result)
        code_settings = self.read_json(self.code_live)
        cursor_settings = self.read_json(self.cursor_live)
        self.assertEqual(code_settings["objectSetting"], {"fromShared": True})
        self.assertEqual(code_settings["ignoredSetting"], "code-live")
        self.assertEqual(code_settings["codeIgnoredSetting"], "code-live")
        self.assertEqual(code_settings["liveOnly"], "code")
        self.assertIs(code_settings["managedFalse"], False)
        self.assertIsNone(code_settings["managedNull"])
        self.assertEqual(code_settings["managedLargeInteger"], 9007199254740993)
        self.assertEqual(
            code_settings["managedMergeKey"],
            {"<<": {"nested": True}, "keep": 2},
        )
        self.assertEqual(code_settings["liveLargeInteger"], 9007199254740993)
        self.assertEqual(
            code_settings["liveMergeKey"],
            {"<<": {"nested": True}, "keep": 2},
        )
        self.assertEqual(code_settings["url"], "https://example.com/a//b")
        self.assertEqual(code_settings["literal"], "/* not a comment */")
        self.assertEqual(
            code_settings["escaped"], 'quote: " // still a string'
        )
        self.assertEqual(code_settings["commaLiteral"], ",}")
        self.assertEqual(cursor_settings["objectSetting"], {"fromCursor": True})
        self.assertEqual(cursor_settings["ignoredSetting"], "cursor-live")
        self.assertEqual(cursor_settings["liveOnly"], "cursor")
        self.assertEqual(stat.S_IMODE(self.code_live.stat().st_mode), code_mode_before)
        self.assertEqual(
            stat.S_IMODE(self.cursor_live.stat().st_mode), cursor_mode_before
        )

        code_after_first = self.code_live.read_bytes()
        cursor_after_first = self.cursor_live.read_bytes()
        code_stat_after_first = self.code_live.stat()
        cursor_stat_after_first = self.cursor_live.stat()
        second_result = self.run_apply()

        self.assert_apply_status(0, second_result)
        self.assertEqual(self.code_live.read_bytes(), code_after_first)
        self.assertEqual(self.cursor_live.read_bytes(), cursor_after_first)
        self.assertEqual(self.code_live.stat().st_ino, code_stat_after_first.st_ino)
        self.assertEqual(
            self.code_live.stat().st_mtime_ns,
            code_stat_after_first.st_mtime_ns,
        )
        self.assertEqual(self.cursor_live.stat().st_ino, cursor_stat_after_first.st_ino)
        self.assertEqual(
            self.cursor_live.stat().st_mtime_ns,
            cursor_stat_after_first.st_mtime_ns,
        )

    def test_rejects_jq_without_literal_number_preservation(self) -> None:
        (self.source_dir / "shared.json").write_text("{}\n")
        self.code_live.write_text('{"original": "code"}\n')
        self.cursor_live.write_text('{"original": "cursor"}\n')
        code_before = self.code_live.read_bytes()
        cursor_before = self.cursor_live.read_bytes()

        shim_dir = self.home / ".test-bin"
        shim_dir.mkdir()
        jq_shim = shim_dir / "jq"
        jq_shim.write_text(
            "#!/bin/sh\nprintf '%s\\n' '{\"value\":9007199254740992}'\n"
        )
        jq_shim.chmod(jq_shim.stat().st_mode | stat.S_IXUSR)

        result = self.run_apply(
            {"PATH": f"{shim_dir}{os.pathsep}{os.environ['PATH']}"}
        )

        self.assert_apply_status(1, result)
        self.assertIn("literal-number preservation", result.stderr)
        self.assertEqual(self.code_live.read_bytes(), code_before)
        self.assertEqual(self.cursor_live.read_bytes(), cursor_before)

    def test_parse_failure_is_atomic(self) -> None:
        (self.source_dir / "shared.json").write_text('{"managed": true}\n')
        self.code_live.write_text('{"original": "code"}\n')
        self.cursor_live.write_text('{"broken": /* unterminated\n')
        code_before = self.code_live.read_bytes()
        cursor_before = self.cursor_live.read_bytes()

        result = self.run_apply()

        self.assert_apply_status(1, result)
        self.assertEqual(self.code_live.read_bytes(), code_before)
        self.assertEqual(self.cursor_live.read_bytes(), cursor_before)

    def test_multiple_json_documents_are_rejected_atomically(self) -> None:
        (self.source_dir / "shared.json").write_text('{"managed": true}\n')
        self.code_live.write_text('{"first": true}\n{"second": true}\n')
        self.cursor_live.write_text('{"original": "cursor"}\n')
        code_before = self.code_live.read_bytes()
        cursor_before = self.cursor_live.read_bytes()

        result = self.run_apply()

        self.assert_apply_status(1, result)
        self.assertEqual(self.code_live.read_bytes(), code_before)
        self.assertEqual(self.cursor_live.read_bytes(), cursor_before)

    def test_multiple_managed_or_ignored_documents_are_rejected(self) -> None:
        self.code_live.write_text("{}\n")
        self.cursor_live.write_text("{}\n")

        with self.subTest(layer="managed"):
            (self.source_dir / "shared.json").write_text("{}\n{}\n")
            self.assert_apply_status(1, self.run_apply())

        with self.subTest(layer="ignored"):
            (self.source_dir / "shared.json").write_text("{}\n")
            (self.source_dir / "ignored.json").write_text("[]\n[]\n")
            self.assert_apply_status(1, self.run_apply())

    def test_invalid_empty_jsonc_entries_are_rejected_atomically(self) -> None:
        (self.source_dir / "shared.json").write_text("{}\n")
        self.cursor_live.write_text('{"original": "cursor"}\n')

        for invalid in ("{,}\n", '{"items": [,]}\n', '{"items": [1,,]}\n'):
            with self.subTest(invalid=invalid):
                self.code_live.write_text(invalid)
                code_before = self.code_live.read_bytes()
                cursor_before = self.cursor_live.read_bytes()

                result = self.run_apply()

                self.assert_apply_status(1, result)
                self.assertEqual(self.code_live.read_bytes(), code_before)
                self.assertEqual(self.cursor_live.read_bytes(), cursor_before)

    def test_duplicate_live_keys_are_canonicalized_before_override(self) -> None:
        (self.source_dir / "shared.json").write_text('{"managed": 4}\n')
        self.code_live.write_text('{"managed": 1, "managed": 2}\n')
        self.cursor_live.write_text("{}\n")

        result = self.run_apply()

        self.assert_apply_status(0, result)
        self.assertEqual(self.read_json(self.code_live)["managed"], 4)
        self.assertEqual(self.code_live.read_text().count('"managed"'), 1)

    def test_read_failure_is_atomic(self) -> None:
        (self.source_dir / "shared.json").write_text('{"managed": true}\n')
        self.code_live.write_text('{"original": "code"}\n')
        self.cursor_live.write_text('{"original": "cursor"}\n')
        code_before = self.code_live.read_bytes()
        cursor_before = self.cursor_live.read_bytes()

        shim_dir = self.home / ".test-bin"
        shim_dir.mkdir()
        cat_shim = shim_dir / "cat"
        cat_shim.write_text(
            textwrap.dedent(
                """\
                #!/bin/sh
                if [ "$1" = "--" ] && [ "$2" = "$VSCODE_SETTINGS_TEST_FAIL_READ" ]; then
                    printf 'cat: forced read failure: %s\\n' "$2" >&2
                    exit 1
                fi
                exec "$VSCODE_SETTINGS_TEST_REAL_CAT" "$@"
                """
            )
        )
        cat_shim.chmod(cat_shim.stat().st_mode | stat.S_IXUSR)
        result = self.run_apply(
            {
                "PATH": f"{shim_dir}{os.pathsep}{os.environ['PATH']}",
                "VSCODE_SETTINGS_TEST_FAIL_READ": str(self.cursor_live),
                "VSCODE_SETTINGS_TEST_REAL_CAT": self.cat,
            }
        )

        self.assert_apply_status(1, result)
        self.assertEqual(self.code_live.read_bytes(), code_before)
        self.assertEqual(self.cursor_live.read_bytes(), cursor_before)

    def test_invalid_utf8_is_rejected_atomically(self) -> None:
        (self.source_dir / "shared.json").write_text('{"managed": true}\n')
        self.code_live.write_bytes(b'{"liveOnly": "\xff"}\n')
        self.cursor_live.write_text('{"original": "cursor"}\n')
        code_before = self.code_live.read_bytes()
        cursor_before = self.cursor_live.read_bytes()

        result = self.run_apply()

        self.assert_apply_status(1, result)
        self.assertIn("invalid UTF-8", result.stderr)
        self.assertEqual(self.code_live.read_bytes(), code_before)
        self.assertEqual(self.cursor_live.read_bytes(), cursor_before)

    def test_raw_nul_is_rejected_atomically(self) -> None:
        (self.source_dir / "shared.json").write_text('{"managed": true}\n')
        self.code_live.write_bytes(b'{"original": "code"}\x00')
        self.cursor_live.write_text('{"original": "cursor"}\n')
        code_before = self.code_live.read_bytes()
        cursor_before = self.cursor_live.read_bytes()

        result = self.run_apply()

        self.assert_apply_status(1, result)
        self.assertIn("raw NUL", result.stderr)
        self.assertEqual(self.code_live.read_bytes(), code_before)
        self.assertEqual(self.cursor_live.read_bytes(), cursor_before)

    def test_replacement_failure_rolls_back_an_earlier_target(self) -> None:
        (self.source_dir / "shared.json").write_text('{"managed": true}\n')
        self.code_live.write_text('{"original": "code"}\n')
        self.cursor_live.write_text('{"original": "cursor"}\n')
        code_before = self.code_live.read_bytes()
        cursor_before = self.cursor_live.read_bytes()

        shim_dir = self.home / ".test-bin"
        shim_dir.mkdir()
        mv_shim = shim_dir / "mv"
        mv_shim.write_text(
            textwrap.dedent(
                """\
                #!/bin/sh
                case "$1" in
                  *.tmp.*)
                    if [ "$2" = "$VSCODE_SETTINGS_TEST_FAIL_REPLACE" ]; then
                      printf 'mv: forced replacement failure: %s\\n' "$2" >&2
                      exit 1
                    fi
                    ;;
                esac
                exec "$VSCODE_SETTINGS_TEST_REAL_MV" "$@"
                """
            )
        )
        mv_shim.chmod(mv_shim.stat().st_mode | stat.S_IXUSR)

        result = self.run_apply(
            {
                "PATH": f"{shim_dir}{os.pathsep}{os.environ['PATH']}",
                "VSCODE_SETTINGS_TEST_FAIL_REPLACE": str(self.cursor_live),
                "VSCODE_SETTINGS_TEST_REAL_MV": self.mv,
            }
        )

        self.assert_apply_status(1, result)
        self.assertEqual(self.code_live.read_bytes(), code_before)
        self.assertEqual(self.cursor_live.read_bytes(), cursor_before)
        self.assertEqual(list(self.home.rglob("settings.json.tmp.*")), [])
        self.assertEqual(list(self.home.rglob("settings.json.backup.*")), [])

    def test_replacement_failure_removes_an_earlier_new_target(self) -> None:
        (self.source_dir / "shared.json").write_text('{"managed": true}\n')
        self.cursor_live.write_text('{"original": "cursor"}\n')
        cursor_before = self.cursor_live.read_bytes()

        shim_dir = self.home / ".test-bin"
        shim_dir.mkdir()
        mv_shim = shim_dir / "mv"
        mv_shim.write_text(
            textwrap.dedent(
                """\
                #!/bin/sh
                case "$1" in
                  *.tmp.*)
                    if [ "$2" = "$VSCODE_SETTINGS_TEST_FAIL_REPLACE" ]; then
                      exit 1
                    fi
                    ;;
                esac
                exec "$VSCODE_SETTINGS_TEST_REAL_MV" "$@"
                """
            )
        )
        mv_shim.chmod(mv_shim.stat().st_mode | stat.S_IXUSR)

        result = self.run_apply(
            {
                "PATH": f"{shim_dir}{os.pathsep}{os.environ['PATH']}",
                "VSCODE_SETTINGS_TEST_FAIL_REPLACE": str(self.cursor_live),
                "VSCODE_SETTINGS_TEST_REAL_MV": self.mv,
            }
        )

        self.assert_apply_status(1, result)
        self.assertFalse(self.code_live.exists())
        self.assertEqual(self.cursor_live.read_bytes(), cursor_before)
        self.assertEqual(list(self.home.rglob("settings.json.tmp.*")), [])
        self.assertEqual(list(self.home.rglob("settings.json.backup.*")), [])

    def test_non_regular_live_target_is_rejected_atomically(self) -> None:
        (self.source_dir / "shared.json").write_text('{"managed": true}\n')
        self.code_live.write_text('{"original": "code"}\n')
        self.cursor_live.mkdir()
        code_before = self.code_live.read_bytes()

        result = self.run_apply()

        self.assert_apply_status(1, result)
        self.assertIn("not a regular file", result.stderr)
        self.assertEqual(self.code_live.read_bytes(), code_before)
        self.assertTrue(self.cursor_live.is_dir())
        self.assertEqual(list(self.cursor_live.iterdir()), [])

    def test_symlink_live_target_is_rejected_atomically(self) -> None:
        (self.source_dir / "shared.json").write_text('{"managed": true}\n')
        real_code_live = self.home / "real-code-settings.json"
        real_code_live.write_text('{"original": "code"}\n')
        self.code_live.symlink_to(real_code_live)
        self.cursor_live.write_text('{"original": "cursor"}\n')
        code_before = real_code_live.read_bytes()
        cursor_before = self.cursor_live.read_bytes()

        result = self.run_apply()

        self.assert_apply_status(1, result)
        self.assertIn("not a regular file", result.stderr)
        self.assertTrue(self.code_live.is_symlink())
        self.assertEqual(real_code_live.read_bytes(), code_before)
        self.assertEqual(self.cursor_live.read_bytes(), cursor_before)

    def test_non_regular_optional_managed_layer_is_rejected_atomically(self) -> None:
        (self.source_dir / "shared.json").write_text('{"managed": true}\n')
        (self.source_dir / "code.json").mkdir()
        self.code_live.write_text('{"original": "code"}\n')
        self.cursor_live.write_text('{"original": "cursor"}\n')
        code_before = self.code_live.read_bytes()
        cursor_before = self.cursor_live.read_bytes()

        result = self.run_apply()

        self.assert_apply_status(1, result)
        self.assertIn("settings layer is not a regular file", result.stderr)
        self.assertEqual(self.code_live.read_bytes(), code_before)
        self.assertEqual(self.cursor_live.read_bytes(), cursor_before)

    def test_non_regular_optional_ignored_input_is_rejected_atomically(self) -> None:
        (self.source_dir / "shared.json").write_text('{"managed": true}\n')
        (self.source_dir / "ignored.json").mkdir()
        self.code_live.write_text('{"managed": "code-live"}\n')
        self.cursor_live.write_text('{"managed": "cursor-live"}\n')
        code_before = self.code_live.read_bytes()
        cursor_before = self.cursor_live.read_bytes()

        result = self.run_apply()

        self.assert_apply_status(1, result)
        self.assertIn("ignored input is not a regular file", result.stderr)
        self.assertEqual(self.code_live.read_bytes(), code_before)
        self.assertEqual(self.cursor_live.read_bytes(), cursor_before)

    def test_symlink_managed_and_ignored_inputs_are_rejected_atomically(self) -> None:
        shared_path = self.source_dir / "shared.json"
        shared_path.write_text('{"managed": true}\n')
        self.code_live.write_text('{"original": "code"}\n')
        self.cursor_live.write_text('{"original": "cursor"}\n')
        code_before = self.code_live.read_bytes()
        cursor_before = self.cursor_live.read_bytes()

        fixtures = {
            "shared.json": self.home / "shared-real.json",
            "code.json": self.home / "code-real.json",
            "ignored.json": self.home / "ignored-real.json",
        }
        fixtures["shared.json"].write_text('{"managed": true}\n')
        fixtures["code.json"].write_text('{"code": true}\n')
        fixtures["ignored.json"].write_text('["local"]\n')

        for name, target in fixtures.items():
            with self.subTest(name=name):
                source = self.source_dir / name
                original = source.read_bytes() if source.exists() else None
                source.unlink(missing_ok=True)
                source.symlink_to(target)

                result = self.run_apply()

                self.assert_apply_status(1, result)
                self.assertIn("not a regular file", result.stderr)
                self.assertEqual(self.code_live.read_bytes(), code_before)
                self.assertEqual(self.cursor_live.read_bytes(), cursor_before)

                source.unlink()
                if original is not None:
                    source.write_bytes(original)

    def test_compare_error_does_not_replace_unchanged_targets(self) -> None:
        (self.source_dir / "shared.json").write_text('{"managed": true}\n')
        self.code_live.write_text("{}\n")
        self.cursor_live.write_text("{}\n")
        self.assert_apply_status(0, self.run_apply())
        code_before = self.code_live.read_bytes()
        cursor_before = self.cursor_live.read_bytes()
        code_stat_before = self.code_live.stat()
        cursor_stat_before = self.cursor_live.stat()

        shim_dir = self.home / ".test-bin"
        shim_dir.mkdir()
        cmp_shim = shim_dir / "cmp"
        cmp_shim.write_text(
            "#!/bin/sh\n"
            'case "$2" in\n'
            "  *.tmp.*) exit 2 ;;\n"
            "esac\n"
            'exec "$VSCODE_SETTINGS_TEST_REAL_CMP" "$@"\n'
        )
        cmp_shim.chmod(cmp_shim.stat().st_mode | stat.S_IXUSR)

        result = self.run_apply(
            {
                "PATH": f"{shim_dir}{os.pathsep}{os.environ['PATH']}",
                "VSCODE_SETTINGS_TEST_REAL_CMP": self.cmp,
            }
        )

        self.assert_apply_status(1, result)
        self.assertIn("failed to compare", result.stderr)
        self.assertEqual(self.code_live.read_bytes(), code_before)
        self.assertEqual(self.cursor_live.read_bytes(), cursor_before)
        self.assertEqual(self.code_live.stat().st_ino, code_stat_before.st_ino)
        self.assertEqual(self.cursor_live.stat().st_ino, cursor_stat_before.st_ino)

    def test_rejects_non_object_managed_layer(self) -> None:
        (self.source_dir / "shared.json").write_text("[]\n")

        result = self.run_apply()

        self.assert_apply_status(1, result)

    def test_rejects_non_standard_json_constants(self) -> None:
        (self.source_dir / "shared.json").write_text("{}\n")
        self.code_live.write_text('{"value": NaN}\n')
        self.cursor_live.write_text("{}\n")

        result = self.run_apply()

        self.assert_apply_status(1, result)

    def test_rejects_non_standard_json_constants_in_managed_files(self) -> None:
        (self.source_dir / "shared.json").write_text('{"value": NaN}\n')

        result = self.run_apply()

        self.assert_apply_status(1, result)

    def test_rejects_non_standard_json_constants_in_ignored_files(self) -> None:
        (self.source_dir / "shared.json").write_text("{}\n")
        (self.source_dir / "ignored.json").write_text("[NaN]\n")

        result = self.run_apply()

        self.assert_apply_status(1, result)

    def test_rejects_non_standard_json_number_forms(self) -> None:
        (self.source_dir / "shared.json").write_text("{}\n")
        self.cursor_live.write_text("{}\n")

        for number in ("+1", "01", ".5", "1."):
            with self.subTest(number=number):
                self.code_live.write_text(f'{{"value": {number}}}\n')
                self.assert_apply_status(1, self.run_apply())

    def test_rejects_out_of_range_json_numbers(self) -> None:
        (self.source_dir / "shared.json").write_text("{}\n")
        self.code_live.write_text('{"value": 1e999}\n')
        self.cursor_live.write_text("{}\n")

        self.assert_apply_status(1, self.run_apply())

    def test_comments_do_not_join_invalid_json_tokens(self) -> None:
        (self.source_dir / "shared.json").write_text("{}\n")
        self.code_live.write_text('{"value": 1/* comment */2}\n')
        self.cursor_live.write_text("{}\n")

        result = self.run_apply()

        self.assert_apply_status(1, result)

    def test_empty_and_comment_only_existing_live_settings_are_rejected(self) -> None:
        (self.source_dir / "shared.json").write_text('{"managed": true}\n')
        self.cursor_live.write_text('{"original": "cursor"}\n')

        for invalid in (b"", b"// No settings yet.\n/* Still empty. */\n"):
            with self.subTest(invalid=invalid):
                self.code_live.write_bytes(invalid)
                code_before = self.code_live.read_bytes()
                cursor_before = self.cursor_live.read_bytes()

                result = self.run_apply()

                self.assert_apply_status(1, result)
                self.assertEqual(self.code_live.read_bytes(), code_before)
                self.assertEqual(self.cursor_live.read_bytes(), cursor_before)

    def test_missing_live_settings_start_as_empty_objects(self) -> None:
        (self.source_dir / "shared.json").write_text('{"managed": true}\n')

        result = self.run_apply()

        self.assert_apply_status(0, result)
        self.assertEqual(self.read_json(self.code_live), {"managed": True})
        self.assertEqual(self.read_json(self.cursor_live), {"managed": True})


if __name__ == "__main__":
    unittest.main()
