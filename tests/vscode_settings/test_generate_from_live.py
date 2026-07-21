from __future__ import annotations

import codecs
import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[2]
GENERATOR = ROOT / ".agents/skills/vscode-settings/scripts/generate-from-live.py"
JSONC_HELPER = (
    ROOT / ".agents/skills/vscode-settings/scripts/vscode_settings_jsonc.py"
)


def load_generator_module():
    sys.path.insert(0, str(GENERATOR.parent))
    spec = importlib.util.spec_from_file_location("vscode_settings_generator", GENERATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load {GENERATOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_python(script: pathlib.Path, *args: pathlib.Path | str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *(str(arg) for arg in args)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


class JsoncHelperTests(unittest.TestCase):
    def test_accepts_jsonc_without_changing_string_content(self) -> None:
        source = textwrap.dedent(
            r'''
            {
              // Full-line comment.
              "url": "https://example.com/a//b",
              "literal": "/* not a comment */",
              "escaped": "quote: \" // still a string",
              "path": "C:\\temp\\",
              "nested": {
                "enabled": true,
              },
              "items": [
                1,
                2, /* block comment */
              ],
            }
            '''
        ).lstrip()

        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = pathlib.Path(temp_dir) / "settings.json"
            settings_path.write_bytes(
                codecs.BOM_UTF8 + source.replace("\n", "\r\n").encode()
            )

            result = run_python(JSONC_HELPER, settings_path)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(result.stdout),
            {
                "url": "https://example.com/a//b",
                "literal": "/* not a comment */",
                "escaped": 'quote: " // still a string',
                "path": "C:\\temp\\",
                "nested": {"enabled": True},
                "items": [1, 2],
            },
        )

    def test_reports_unterminated_block_comment_coordinates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = pathlib.Path(temp_dir) / "settings.json"
            settings_path.write_text('{\n  "a": /* unfinished\n')

            result = run_python(JSONC_HELPER, settings_path)

        self.assertEqual(result.returncode, 1)
        self.assertIn(f"{settings_path}:2:8: unterminated block comment", result.stderr)

    def test_invalid_utf8_is_reported_without_a_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = pathlib.Path(temp_dir) / "settings.json"
            settings_path.write_bytes(b'{"value": "\xff"}\n')

            result = run_python(JSONC_HELPER, settings_path)

        self.assertEqual(result.returncode, 1)
        self.assertIn(f"Error: failed to read {settings_path}", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_rejects_zero_document_input(self) -> None:
        for source in ("", "// No settings yet.\n/* Still empty. */\n"):
            with self.subTest(source=source), tempfile.TemporaryDirectory() as temp_dir:
                settings_path = pathlib.Path(temp_dir) / "settings.json"
                settings_path.write_text(source)

                result = run_python(JSONC_HELPER, settings_path)

            self.assertEqual(result.returncode, 1)
            self.assertIn("invalid JSONC", result.stderr)

    def test_rejects_non_object_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = pathlib.Path(temp_dir) / "settings.json"
            settings_path.write_text("[1, 2,]\n")

            result = run_python(JSONC_HELPER, settings_path)

        self.assertEqual(result.returncode, 1)
        self.assertIn(f"{settings_path}:1:1: expected a JSON object", result.stderr)

    def test_rejects_non_standard_numeric_constants(self) -> None:
        for constant in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(constant=constant), tempfile.TemporaryDirectory() as temp_dir:
                settings_path = pathlib.Path(temp_dir) / "settings.json"
                settings_path.write_text(
                    f'{{\n  "valid": true,\n  "value": {constant}\n}}\n'
                )

                result = run_python(JSONC_HELPER, settings_path)

            self.assertEqual(result.returncode, 1)
            self.assertIn(f"invalid JSON constant: {constant}", result.stderr)
            self.assertIn(f"{settings_path}:3:12:", result.stderr)

    def test_rejects_out_of_range_json_numbers(self) -> None:
        for number in ("1e999", "1" + ("0" * 400)):
            with self.subTest(number=number), tempfile.TemporaryDirectory() as temp_dir:
                settings_path = pathlib.Path(temp_dir) / "settings.json"
                settings_path.write_text(f'{{\n  "value": {number}\n}}\n')

                result = run_python(JSONC_HELPER, settings_path)

            self.assertEqual(result.returncode, 1)
            self.assertIn(f"JSON number is out of range: {number}", result.stderr)
            self.assertIn(f"{settings_path}:2:12:", result.stderr)

    def test_rejects_invalid_empty_jsonc_entries(self) -> None:
        for source in ("{,}\n", '{"items": [,]}\n'):
            with self.subTest(source=source), tempfile.TemporaryDirectory() as temp_dir:
                settings_path = pathlib.Path(temp_dir) / "settings.json"
                settings_path.write_text(source)

                result = run_python(JSONC_HELPER, settings_path)

            self.assertEqual(result.returncode, 1)
            self.assertIn("invalid JSONC", result.stderr)


class GenerateFromLiveTests(unittest.TestCase):
    def test_classifies_complete_jsonc_and_honors_ignored_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = pathlib.Path(temp_dir)
            code_path = fixture / "code.jsonc"
            cursor_path = fixture / "cursor.jsonc"
            output_dir = fixture / "output"
            output_dir.mkdir()

            code_path.write_text(
                textwrap.dedent(
                    '''
                    {
                      "shared": {"enabled": true},
                      "code.only": 1, // Code-specific.
                      "ignored.global": "code",
                      "ignored.code": "code",
                      "type.bool-number": true,
                      "type.nested": {"value": false},
                      "yaml.disableSchemaDetection": ["code"],
                    }
                    '''
                )
            )
            cursor_path.write_text(
                textwrap.dedent(
                    '''
                    {
                      /* Cursor keeps the same shared object. */
                      "shared": {"enabled": true},
                      "cursor.only": 2,
                      "ignored.global": "cursor",
                      "ignored.code": "cursor",
                      "type.bool-number": 1,
                      "type.nested": {"value": 0},
                      "yaml.disableSchemaDetection": ["cursor"],
                    }
                    '''
                )
            )
            (output_dir / "ignored.json").write_text('["ignored.global"]\n')
            (output_dir / "code.ignored.json").write_text('["ignored.code"]\n')

            result = run_python(
                GENERATOR,
                "--code",
                code_path,
                "--cursor",
                cursor_path,
                "--out",
                output_dir,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                json.loads((output_dir / "shared.json").read_text()),
                {"shared": {"enabled": True}},
            )
            self.assertEqual(
                json.loads((output_dir / "code.json").read_text()),
                {
                    "code.only": 1,
                    "type.bool-number": True,
                    "type.nested": {"value": False},
                    "yaml.disableSchemaDetection": ["code"],
                },
            )
            self.assertEqual(
                json.loads((output_dir / "cursor.json").read_text()),
                {
                    "cursor.only": 2,
                    "ignored.code": "cursor",
                    "type.bool-number": 1,
                    "type.nested": {"value": 0},
                    "yaml.disableSchemaDetection": ["cursor"],
                },
            )

    def test_keeps_non_list_yaml_values_app_specific(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = pathlib.Path(temp_dir)
            code_path = fixture / "code.json"
            cursor_path = fixture / "cursor.json"
            output_dir = fixture / "output"
            code_path.write_text('{"yaml.disableSchemaDetection": true}\n')
            cursor_path.write_text('{"yaml.disableSchemaDetection": false}\n')

            result = run_python(
                GENERATOR,
                "--code",
                code_path,
                "--cursor",
                cursor_path,
                "--out",
                output_dir,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads((output_dir / "shared.json").read_text()), {})
            self.assertEqual(
                json.loads((output_dir / "code.json").read_text()),
                {"yaml.disableSchemaDetection": True},
            )
            self.assertEqual(
                json.loads((output_dir / "cursor.json").read_text()),
                {"yaml.disableSchemaDetection": False},
            )

    def test_invalid_utf8_is_reported_without_a_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = pathlib.Path(temp_dir)
            code_path = fixture / "code.json"
            cursor_path = fixture / "cursor.json"
            output_dir = fixture / "output"
            code_path.write_bytes(b'{"value": "\xff"}\n')
            cursor_path.write_text("{}\n")

            live_result = run_python(
                GENERATOR,
                "--code",
                code_path,
                "--cursor",
                cursor_path,
                "--out",
                output_dir,
            )

            self.assertEqual(live_result.returncode, 2)
            self.assertNotIn("Traceback", live_result.stderr)

            code_path.write_text("{}\n")
            output_dir.mkdir()
            (output_dir / "ignored.json").write_bytes(b"[\xff]\n")
            ignored_result = run_python(
                GENERATOR,
                "--code",
                code_path,
                "--cursor",
                cursor_path,
                "--out",
                output_dir,
            )

            self.assertEqual(ignored_result.returncode, 2)
            self.assertNotIn("Traceback", ignored_result.stderr)

    def test_non_regular_ignored_input_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = pathlib.Path(temp_dir)
            code_path = fixture / "code.json"
            cursor_path = fixture / "cursor.json"
            output_dir = fixture / "output"
            output_dir.mkdir()
            code_path.write_text("{}\n")
            cursor_path.write_text("{}\n")
            (output_dir / "ignored.json").mkdir()

            result = run_python(
                GENERATOR,
                "--code",
                code_path,
                "--cursor",
                cursor_path,
                "--out",
                output_dir,
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("ignored input is not a regular file", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertFalse((output_dir / "shared.json").exists())
            self.assertFalse((output_dir / "code.json").exists())
            self.assertFalse((output_dir / "cursor.json").exists())

    def test_empty_ignored_input_is_rejected_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = pathlib.Path(temp_dir)
            code_path = fixture / "code.json"
            cursor_path = fixture / "cursor.json"
            output_dir = fixture / "output"
            output_dir.mkdir()
            code_path.write_text('{"code": true}\n')
            cursor_path.write_text('{"cursor": true}\n')
            (output_dir / "ignored.json").write_text("")

            result = run_python(
                GENERATOR,
                "--code",
                code_path,
                "--cursor",
                cursor_path,
                "--out",
                output_dir,
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("invalid JSON", result.stderr)
            self.assertFalse((output_dir / "shared.json").exists())
            self.assertFalse((output_dir / "code.json").exists())
            self.assertFalse((output_dir / "cursor.json").exists())

    def test_symlink_live_and_ignored_inputs_are_rejected(self) -> None:
        for symlink_name in ("code", "ignored"):
            with self.subTest(symlink_name=symlink_name), tempfile.TemporaryDirectory() as temp_dir:
                fixture = pathlib.Path(temp_dir)
                real_code = fixture / "real-code.json"
                code_path = fixture / "code.json"
                cursor_path = fixture / "cursor.json"
                output_dir = fixture / "output"
                output_dir.mkdir()
                real_code.write_text('{"code": true}\n')
                cursor_path.write_text('{"cursor": true}\n')

                if symlink_name == "code":
                    code_path.symlink_to(real_code)
                else:
                    code_path.write_text('{"code": true}\n')
                    real_ignored = fixture / "real-ignored.json"
                    real_ignored.write_text('["local"]\n')
                    (output_dir / "ignored.json").symlink_to(real_ignored)

                result = run_python(
                    GENERATOR,
                    "--code",
                    code_path,
                    "--cursor",
                    cursor_path,
                    "--out",
                    output_dir,
                )

                self.assertEqual(result.returncode, 2)
                self.assertIn("not a regular file", result.stderr)
                self.assertFalse((output_dir / "shared.json").exists())
                self.assertFalse((output_dir / "code.json").exists())
                self.assertFalse((output_dir / "cursor.json").exists())

    def test_out_of_range_number_does_not_write_managed_layers(self) -> None:
        for number in ("1e999", "1" + ("0" * 400)):
            with self.subTest(number=number), tempfile.TemporaryDirectory() as temp_dir:
                fixture = pathlib.Path(temp_dir)
                code_path = fixture / "code.json"
                cursor_path = fixture / "cursor.json"
                output_dir = fixture / "output"
                code_path.write_text(f'{{"value": {number}}}\n')
                cursor_path.write_text("{}\n")

                result = run_python(
                    GENERATOR,
                    "--code",
                    code_path,
                    "--cursor",
                    cursor_path,
                    "--out",
                    output_dir,
                )

                self.assertEqual(result.returncode, 2)
                self.assertNotIn("Traceback", result.stderr)
                self.assertFalse((output_dir / "shared.json").exists())
                self.assertFalse((output_dir / "code.json").exists())
                self.assertFalse((output_dir / "cursor.json").exists())

    def test_invalid_empty_entry_keeps_existing_managed_layers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = pathlib.Path(temp_dir)
            code_path = fixture / "code.json"
            cursor_path = fixture / "cursor.json"
            output_dir = fixture / "output"
            output_dir.mkdir()
            code_path.write_text("{,}\n")
            cursor_path.write_text("{}\n")
            outputs = [
                output_dir / "shared.json",
                output_dir / "code.json",
                output_dir / "cursor.json",
            ]
            for path in outputs:
                path.write_text(f'{{"original": "{path.stem}"}}\n')
            before = {path: path.read_bytes() for path in outputs}

            result = run_python(
                GENERATOR,
                "--code",
                code_path,
                "--cursor",
                cursor_path,
                "--out",
                output_dir,
            )

            self.assertEqual(result.returncode, 2)
            self.assertNotIn("Traceback", result.stderr)
            for path in outputs:
                self.assertEqual(path.read_bytes(), before[path])

    def test_zero_document_live_keeps_existing_managed_layers(self) -> None:
        for source in ("", "// No settings yet.\n/* Still empty. */\n"):
            with self.subTest(source=source), tempfile.TemporaryDirectory() as temp_dir:
                fixture = pathlib.Path(temp_dir)
                code_path = fixture / "code.json"
                cursor_path = fixture / "cursor.json"
                output_dir = fixture / "output"
                output_dir.mkdir()
                code_path.write_text(source)
                cursor_path.write_text("{}\n")
                outputs = [
                    output_dir / "shared.json",
                    output_dir / "code.json",
                    output_dir / "cursor.json",
                ]
                for path in outputs:
                    path.write_text(f'{{"original": "{path.stem}"}}\n')
                before = {path: path.read_bytes() for path in outputs}

                result = run_python(
                    GENERATOR,
                    "--code",
                    code_path,
                    "--cursor",
                    cursor_path,
                    "--out",
                    output_dir,
                )

                self.assertEqual(result.returncode, 2)
                self.assertIn("invalid JSONC", result.stderr)
                for path in outputs:
                    self.assertEqual(path.read_bytes(), before[path])

    def test_output_preparation_failure_keeps_existing_layers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = pathlib.Path(temp_dir)
            code_path = fixture / "code.json"
            cursor_path = fixture / "cursor.json"
            output_dir = fixture / "output"
            output_dir.mkdir()
            code_path.write_text('{"code": true}\n')
            cursor_path.write_text('{"cursor": true}\n')
            shared_output = output_dir / "shared.json"
            code_output = output_dir / "code.json"
            shared_output.write_text('{"original": "shared"}\n')
            code_output.write_text('{"original": "code"}\n')
            (output_dir / "cursor.json").mkdir()
            shared_before = shared_output.read_bytes()
            code_before = code_output.read_bytes()

            result = run_python(
                GENERATOR,
                "--code",
                code_path,
                "--cursor",
                cursor_path,
                "--out",
                output_dir,
            )

            self.assertEqual(result.returncode, 1)
            self.assertNotIn("Traceback", result.stderr)
            self.assertEqual(shared_output.read_bytes(), shared_before)
            self.assertEqual(code_output.read_bytes(), code_before)
            self.assertEqual(list(output_dir.glob("*.tmp")), [])
            self.assertEqual(list(output_dir.glob("*.bak")), [])

    def test_replace_failure_rolls_back_existing_layers(self) -> None:
        generator = load_generator_module()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = pathlib.Path(temp_dir)
            paths = [
                output_dir / "shared.json",
                output_dir / "code.json",
                output_dir / "cursor.json",
            ]
            for path in paths:
                path.write_text(f'{{"original": "{path.stem}"}}\n')
            before = {path: path.read_bytes() for path in paths}
            real_replace = generator.os.replace

            def fail_code_replace(source, destination):
                source_path = pathlib.Path(source)
                destination_path = pathlib.Path(destination)
                if destination_path == paths[1] and source_path.suffix == ".tmp":
                    raise OSError("forced replacement failure")
                return real_replace(source, destination)

            with mock.patch.object(
                generator.os,
                "replace",
                side_effect=fail_code_replace,
            ):
                with self.assertRaisesRegex(OSError, "forced replacement failure"):
                    generator.write_json_layers(
                        [
                            (paths[0], {"new": "shared"}),
                            (paths[1], {"new": "code"}),
                            (paths[2], {"new": "cursor"}),
                        ]
                    )

            for path in paths:
                self.assertEqual(path.read_bytes(), before[path])
            self.assertEqual(list(output_dir.glob("*.tmp")), [])
            self.assertEqual(list(output_dir.glob("*.bak")), [])

    def test_rollback_replace_failure_uses_copy_fallback(self) -> None:
        generator = load_generator_module()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = pathlib.Path(temp_dir)
            paths = [
                output_dir / "shared.json",
                output_dir / "code.json",
                output_dir / "cursor.json",
            ]
            for path in paths:
                path.write_text(f'{{"original": "{path.stem}"}}\n')
            before = {path: path.read_bytes() for path in paths}
            real_replace = generator.os.replace

            def fail_replacement_and_rollback_rename(source, destination):
                source_path = pathlib.Path(source)
                destination_path = pathlib.Path(destination)
                if destination_path == paths[1] and source_path.suffix == ".tmp":
                    raise OSError("forced replacement failure")
                if destination_path == paths[0] and source_path.suffix == ".bak":
                    raise OSError("forced rollback rename failure")
                return real_replace(source, destination)

            with mock.patch.object(
                generator.os,
                "replace",
                side_effect=fail_replacement_and_rollback_rename,
            ):
                with self.assertRaisesRegex(OSError, "forced replacement failure"):
                    generator.write_json_layers(
                        [
                            (paths[0], {"new": "shared"}),
                            (paths[1], {"new": "code"}),
                            (paths[2], {"new": "cursor"}),
                        ]
                    )

            for path in paths:
                self.assertEqual(path.read_bytes(), before[path])
            self.assertEqual(list(output_dir.glob(".*.tmp")), [])
            self.assertEqual(list(output_dir.glob(".*.bak")), [])

    def test_rollback_failure_preserves_recovery_backup(self) -> None:
        generator = load_generator_module()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = pathlib.Path(temp_dir)
            paths = [
                output_dir / "shared.json",
                output_dir / "code.json",
                output_dir / "cursor.json",
            ]
            for path in paths:
                path.write_text(f'{{"original": "{path.stem}"}}\n')
            before = {path: path.read_bytes() for path in paths}
            real_replace = generator.os.replace
            real_copy2 = generator.shutil.copy2

            def fail_replacement_and_rollback_rename(source, destination):
                source_path = pathlib.Path(source)
                destination_path = pathlib.Path(destination)
                if destination_path == paths[1] and source_path.suffix == ".tmp":
                    raise OSError("forced replacement failure")
                if destination_path == paths[0] and source_path.suffix == ".bak":
                    raise OSError("forced rollback rename failure")
                return real_replace(source, destination)

            def fail_rollback_copy(source, destination, *args, **kwargs):
                source_path = pathlib.Path(source)
                destination_path = pathlib.Path(destination)
                if destination_path == paths[0] and source_path.suffix == ".bak":
                    raise OSError("forced rollback copy failure")
                return real_copy2(source, destination, *args, **kwargs)

            with (
                mock.patch.object(
                    generator.os,
                    "replace",
                    side_effect=fail_replacement_and_rollback_rename,
                ),
                mock.patch.object(
                    generator.shutil,
                    "copy2",
                    side_effect=fail_rollback_copy,
                ),
            ):
                with self.assertRaisesRegex(
                    OSError,
                    "recovery backups preserved",
                ):
                    generator.write_json_layers(
                        [
                            (paths[0], {"new": "shared"}),
                            (paths[1], {"new": "code"}),
                            (paths[2], {"new": "cursor"}),
                        ]
                    )

            self.assertNotEqual(paths[0].read_bytes(), before[paths[0]])
            self.assertEqual(paths[1].read_bytes(), before[paths[1]])
            self.assertEqual(paths[2].read_bytes(), before[paths[2]])
            backups = list(output_dir.glob(".*.bak"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_bytes(), before[paths[0]])
            self.assertEqual(list(output_dir.glob(".*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
