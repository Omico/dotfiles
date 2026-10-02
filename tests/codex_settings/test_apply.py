import importlib.util
import os
from pathlib import Path
import stat
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("codex_settings", ROOT / "app-settings/codex/apply.py")
sync = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync)


class MergeTests(unittest.TestCase):
    def merge(self, live, shared, local=""):
        return sync.plan(sync.parse(live.encode()), sync.parse(shared.encode()), sync.parse(local.encode()))

    def test_leaf_update_keeps_runtime_state_and_comments(self):
        live = '''# Keep this header
model = "old" # Model comment
unknown = 17
[desktop]
codeFontSize = 12
future = "keep"
[desktop."open-in-target-preferences".perPath]
"/example/project" = "example-editor"
[mcp_servers.example_server]
enabled = false
url = "http://127.0.0.1:1234/stream"
[hooks.state.example_hook]
trusted_hash = "sha256:example"
[model_providers.example_provider]
env_key = "EXAMPLE_PROVIDER_API_KEY"
'''
        candidate, changed = self.merge(live, '[settings]\nmodel = "new"\n[settings.desktop]\ncodeFontSize = 16\n')
        expected = sync.parse(live.encode())
        expected['model'] = 'new'
        expected['desktop']['codeFontSize'] = 16
        self.assertEqual(sync.parse(candidate), expected)
        self.assertIn(b'# Keep this header', candidate)
        self.assertIn(b'# Model comment', candidate)
        self.assertEqual(set(changed), {('model',), ('desktop', 'codeFontSize')})

    def test_release_does_not_delete(self):
        candidate, changed = self.merge('model = "local"\n', 'remove = []\n')
        self.assertEqual(sync.parse(candidate)['model'], 'local')
        self.assertEqual(changed, [])

    def test_release_last_field_keeps_empty_shared_table(self):
        candidate, changed = self.merge('[desktop]\nsize=12\n', '[settings.desktop]\n')
        self.assertEqual(sync.parse(candidate), {'desktop': {'size': 12}})
        self.assertEqual(changed, [])

    def test_remove_last_field_with_empty_shared_table(self):
        shared = 'remove=[["plugins","a@b","enabled"]]\n[settings.plugins."a@b"]\n'
        live = '[plugins."a@b"]\nenabled=true\nunknown="local"\n'
        candidate, changed = self.merge(live, shared)
        self.assertEqual(sync.parse(candidate)['plugins']['a@b'], {'unknown': 'local'})
        self.assertEqual(changed, [('plugins', 'a@b', 'enabled')])
        self.assertEqual(self.merge(candidate.decode(), shared), (candidate, []))
        kept, changes = self.merge(live, shared, 'preserve=[["plugins","a@b","enabled"]]')
        self.assertEqual(sync.parse(kept), sync.parse(live.encode()))
        self.assertEqual(changes, [])

    def test_empty_shared_tables_do_not_create_live_tables(self):
        candidate, changed = self.merge('model="local"\n', '[settings.desktop]\n[settings.plugins."a@b"]\n')
        self.assertEqual(sync.parse(candidate), {'model': 'local'})
        self.assertEqual(changed, [])

    def test_explicit_removal_and_idempotence(self):
        shared = 'remove = [["desktop", "size"]]\n[settings]\nmodel="new"\n'
        candidate, _ = self.merge('[desktop]\nsize=12\nunknown=true\n', shared)
        self.assertEqual(sync.parse(candidate)['desktop'], {'unknown': True})
        second, changed = self.merge(candidate.decode(), shared)
        self.assertEqual(candidate, second)
        self.assertEqual(changed, [])

    def test_local_preserve_wins_over_set_and_delete_and_absence(self):
        candidate, changed = self.merge('model="local"\nsize=12\n', 'remove=[["size"]]\n[settings]\nmodel="shared"\nnew=1\n', 'preserve=[["model"],["size"],["new"]]\n')
        self.assertEqual(sync.parse(candidate), {'model': 'local', 'size': 12})
        self.assertEqual(changed, [])

    def test_app_rewrite_is_restored(self):
        candidate, changed = self.merge('[desktop]\nsize=10\n', '[settings.desktop]\nsize=16\n')
        self.assertEqual(sync.parse(candidate)['desktop']['size'], 16)
        self.assertEqual(changed, [('desktop', 'size')])

    def test_literal_dotted_plugin_and_unknown_sibling(self):
        candidate, _ = self.merge('[plugins."a.b@c"]\nenabled=false\nstate="local"\n', '[settings.plugins."a.b@c"]\nenabled=true\n')
        self.assertEqual(sync.parse(candidate)['plugins']['a.b@c'], {'enabled': True, 'state': 'local'})

    def test_bool_and_integer_are_not_equal_preferences(self):
        candidate, changed = self.merge('x=true\n', '[settings]\nx=1\n')
        self.assertEqual(changed, [('x',)])
        self.assertIsInstance(sync.parse(candidate)['x'], int)

    def test_arrays_replace_as_a_unit(self):
        candidate, _ = self.merge('x=["a","b"]\n', '[settings]\nx=["c"]\n')
        self.assertEqual(sync.parse(candidate)['x'], ['c'])

    def test_invalid_controls_conflicts_and_table_deletion_fail(self):
        cases = [
            ('x=1', '[settings]\nx=2\n', 'perserve=[]'),
            ('x=1', 'remove=[["x"]]\n[settings]\nx=2', ''),
            ('[x]\ny=1', 'remove=[["x"]]', ''),
            ('x=1', '[settings.x]\ny=2', ''),
            ('[x]\ny=1', '[settings]\nx=2', ''),
            ('', 'remove=[["x"],["x","y"]]', ''),
            ('', 'remove=["x"]', ''),
            ('', 'unknown=true', ''),
        ]
        for live, shared, local in cases:
            with self.subTest(shared=shared, local=local), self.assertRaises(ValueError):
                self.merge(live, shared, local)

    def test_invalid_toml_fails(self):
        with self.assertRaises(Exception):
            self.merge('x = [', '[settings]\nx=1')

    def test_valid_unknown_nan_and_date_survive(self):
        candidate, _ = self.merge('unknown=nan\ndate=1979-05-27T07:32:00Z\n', '[settings]\nmodel="new"')
        self.assertIn(b'unknown=nan', candidate)
        self.assertIn(b'date=1979-05-27T07:32:00Z', candidate)

    def test_cli_writes_isolated_home_then_is_noop(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            helper = folder / 'apply.py'
            shutil.copyfile(sync.__file__, helper)
            (folder / 'settings.shared.toml').write_text('[settings]\nmodel="new"\n')
            runtime = folder / 'runtime'
            env = dict(os.environ, HOME=str(folder), CODEX_HOME=str(runtime))
            command = [sys.executable, str(helper)]
            subprocess.run(command + ['--dry-run'], env=env, check=True, capture_output=True)
            self.assertFalse(runtime.exists())
            pending = subprocess.run(command, env=env, capture_output=True, text=True)
            self.assertEqual(pending.returncode, 2)
            self.assertIn('--offline', pending.stderr)
            self.assertFalse(runtime.exists())
            # Isolate the process inventory; the actual test host can run Codex.
            fake_bin = folder / 'bin'
            fake_bin.mkdir()
            ps = fake_bin / 'ps'
            ps.write_text('#!/bin/sh\nprintf "/sbin/launchd\\n"\n')
            ps.chmod(0o755)
            env['PATH'] = str(fake_bin) + os.pathsep + env['PATH']
            subprocess.run(command + ['--offline'], env=env, check=True, capture_output=True)
            live = runtime / 'config.toml'
            self.assertEqual(sync.parse(live.read_bytes())['model'], 'new')
            before = sync.identity(live.stat())
            subprocess.run(command, env=env, check=True, capture_output=True)
            self.assertEqual(before, sync.identity(live.stat()))
            self.assertFalse((runtime / 'settings-sync-backups').exists())
            (folder / 'settings.shared.toml').write_text('[settings]\nmodel="changed"\n')
            ps.write_text('#!/bin/sh\nprintf "/Applications/ChatGPT.app/Contents/MacOS/ChatGPT\\n"\n')
            blocked = subprocess.run(command + ['--offline'], env=env, capture_output=True, text=True)
            self.assertEqual(blocked.returncode, 1)
            self.assertIn('is running', blocked.stderr)
            self.assertEqual(before, sync.identity(live.stat()))
            self.assertFalse((runtime / 'settings-sync-backups').exists())

    def test_checked_in_selection_excludes_runtime_and_machine_data(self):
        doc = sync.parse((ROOT / 'app-settings/codex/settings.shared.toml').read_bytes())
        fields = dict(sync.leaves(doc['settings']))
        self.assertFalse({'mcp_servers', 'hooks', 'projects', 'model_providers', 'marketplaces', 'skills', 'apps'} & {p[0] for p in fields})
        for path, value in fields.items():
            self.assertNotIn('/Users/', str(value))
            self.assertNotIn('127.0.0.1', str(value))
            self.assertNotIn('trusted_hash', path)
        self.assertIn(('desktop', 'appearanceTheme'), fields)


class PublishTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.target = Path(self.directory.name) / 'config.toml'
        self.target.write_bytes(b'# local\nx=1\n')
        self.target.chmod(0o640)
        offline = patch.object(sync, 'require_offline')
        offline.start()
        self.addCleanup(offline.stop)

    def test_writer_detected_before_replace_aborts(self):
        snapshot = sync.read(self.target)
        with patch.object(sync, 'require_offline', side_effect=[None, ValueError('Writer started')]), self.assertRaises(ValueError):
            sync.publish(self.target, snapshot, b'x=2\n', [])
        self.assertEqual(self.target.read_bytes(), snapshot[0])
        self.assertFalse(list(self.target.parent.glob('.codex-settings-*')))

    def test_default_pending_changes_never_reach_publisher(self):
        shared = Path(sync.__file__).parent / 'settings.shared.toml'
        local = Path.home() / '.config/codex-settings/settings.local.toml'
        original_read = sync.read
        def fixture(path, optional=False):
            if path == shared:
                return b'[settings]\nx=2\n', None
            if path == local:
                return b'', None
            return original_read(path, optional)
        snapshot = sync.read(self.target)
        with patch.dict(os.environ, CODEX_HOME=str(self.target.parent)), patch('sys.argv', ['apply.py']), patch.object(sync, 'read', side_effect=fixture), patch.object(sync, 'publish') as publish:
            with self.assertRaises(SystemExit) as result:
                sync.main()
            self.assertEqual(result.exception.code, 2)
            publish.assert_not_called()
        self.assertEqual(sync.read(self.target)[0], snapshot[0])
        self.assertEqual(sync.identity(self.target.stat()), sync.identity(snapshot[1]))
        self.assertEqual(list(self.target.parent.iterdir()), [self.target])

    def test_backup_exact_and_modes_preserved(self):
        snapshot = sync.read(self.target)
        backup = sync.publish(self.target, snapshot, b'x=2\n', [])
        self.assertEqual(backup.read_bytes(), snapshot[0])
        self.assertEqual(self.target.read_bytes(), b'x=2\n')
        self.assertEqual(stat.S_IMODE(self.target.stat().st_mode), 0o640)
        self.assertEqual(stat.S_IMODE(backup.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(backup.parent.stat().st_mode), 0o700)

    def test_concurrent_change_is_not_overwritten(self):
        snapshot = sync.read(self.target)
        self.target.write_bytes(b'x=3\n')
        with self.assertRaises(ValueError):
            sync.publish(self.target, snapshot, b'x=2\n', [])
        self.assertEqual(self.target.read_bytes(), b'x=3\n')

    def test_change_during_backup_is_not_overwritten(self):
        snapshot = sync.read(self.target)
        original = sync.unchanged
        calls = []
        def race(path, prior):
            calls.append(path)
            if len(calls) == 2:
                self.target.write_bytes(b'x=3\n')
            original(path, prior)
        with patch.object(sync, 'unchanged', side_effect=race), self.assertRaises(ValueError):
            sync.publish(self.target, snapshot, b'x=2\n', [])
        self.assertEqual(self.target.read_bytes(), b'x=3\n')

    def test_input_change_aborts(self):
        shared = self.target.parent / 'shared.toml'
        shared.write_bytes(b'x=1\n')
        prior = sync.read(shared)
        shared.write_bytes(b'x=2\n')
        with self.assertRaises(ValueError):
            sync.publish(self.target, sync.read(self.target), b'x=2\n', [(shared, prior)])
        self.assertEqual(self.target.read_bytes(), b'# local\nx=1\n')

    def test_symlink_and_hardlink_rejected(self):
        alias = self.target.parent / 'alias'
        alias.symlink_to(self.target)
        with self.assertRaises(ValueError):
            sync.read(alias)
        alias.unlink()
        os.link(self.target, alias)
        with self.assertRaises(ValueError):
            sync.read(self.target)

    def test_new_file_private(self):
        self.target.unlink()
        self.assertIsNone(sync.publish(self.target, (b'', None), b'x=1\n', []))
        self.assertEqual(stat.S_IMODE(self.target.stat().st_mode), 0o600)

    def test_dry_run_and_noop_do_not_write(self):
        shared = sync.Path(sync.__file__).parent / 'settings.shared.toml'
        local = sync.Path.home() / '.config/codex-settings/settings.local.toml'
        real_read = sync.read
        def read_fixture(path, optional=False):
            if path == shared:
                return b'[settings]\nx=1\n', None
            if path == local:
                return b'', None
            return real_read(path, optional)
        before = self.target.stat()
        for args in [['apply.py'], ['apply.py', '--dry-run']]:
            with patch.dict(os.environ, CODEX_HOME=str(self.target.parent)), patch('sys.argv', args), patch.object(sync, 'read', side_effect=read_fixture), patch.object(sync, 'publish') as publish:
                sync.main()
                publish.assert_not_called()
        self.assertEqual(before, self.target.stat())


class OfflineTests(unittest.TestCase):
    def test_known_writers_block_offline_apply(self):
        for name in ['codex', '/opt/bin/codex-cli', '/Applications/Codex.app/Contents/MacOS/Codex', '/Applications/ChatGPT.app/Contents/MacOS/ChatGPT', '/opt/bin/apm', '/app/CodexCLI']:
            result = subprocess.CompletedProcess([], 0, stdout=name + '\n', stderr='')
            with self.subTest(name=name), patch.object(sync.subprocess, 'run', return_value=result), self.assertRaises(ValueError):
                sync.require_offline()

    def test_process_inventory_errors_fail_closed(self):
        for error in [FileNotFoundError(), subprocess.TimeoutExpired('ps', 10), subprocess.CalledProcessError(1, 'ps')]:
            with self.subTest(error=error), patch.object(sync.subprocess, 'run', side_effect=error), self.assertRaises(ValueError):
                sync.require_offline()

    def test_unrelated_processes_do_not_block(self):
        result = subprocess.CompletedProcess([], 0, stdout='/sbin/launchd\n/usr/bin/python3\n/usr/bin/fish\n', stderr='')
        with patch.object(sync.subprocess, 'run', return_value=result):
            sync.require_offline()


if __name__ == '__main__':
    unittest.main()
