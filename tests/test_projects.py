"""Project state, hostile names and destructive-operation boundaries."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import datacon
import projects


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.state = datacon.initialise('test', self.root)
        self.manager = projects.Manager('test', self.root, datacon.compose, datacon.environment('test', self.root))
        self.repo = self.root / 'Sample delivery $ path'
        self.repo.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        (self.repo / 'nested').mkdir()
        (self.repo / 'unfinished.txt').write_text('keep me')

    def add(self, name='delivery-a'):
        return self.manager.add(name, str(self.repo), None, 'nested')

    def test_invalid_names_and_escaping_directories_are_rejected(self):
        for name in ('../a', 'A', 'a;drop database', 'x'*33, 'a_b'):
            with self.subTest(name=name), self.assertRaises(projects.ProjectError):
                projects.project_name(name)
        for path in ('../other', '/other', 'nested/../../other', 'a\nb'):
            with self.subTest(path=path), self.assertRaises(projects.ProjectError):
                projects.workdir(path)

    def test_registration_preserves_checkout_and_credentials_on_repeat(self):
        first = self.add()
        password = self.state / 'projects/delivery-a/password'
        before = password.read_bytes()
        self.assertEqual(self.add(), first)
        self.assertEqual(password.read_bytes(), before)
        self.assertEqual((self.repo / 'unfinished.txt').read_text(), 'keep me')
        self.assertFalse((self.repo / '.datacon').exists())
        self.assertNotIn(before.decode().strip(), (self.state / 'projects.json').read_text())

    def test_binding_cannot_be_replaced_or_adopt_missing_credentials(self):
        self.add()
        with self.assertRaises(projects.ProjectError):
            self.manager.add('delivery-a', str(self.repo), None, '.')
        (self.state / 'projects/delivery-a/password').unlink()
        with self.assertRaisesRegex(projects.ProjectError, 'credentials'):
            self.add()

    def test_nested_repository_path_and_symlink_escape_are_rejected(self):
        with self.assertRaises(projects.ProjectError):
            projects.check_host_checkout(self.repo / 'nested', '.')
        (self.repo / 'outside').symlink_to(self.root)
        with self.assertRaises(projects.ProjectError):
            self.manager.add('bad', str(self.repo), None, 'outside')

    def test_compose_uses_exact_bind_source_and_never_creates_missing_paths(self):
        self.add()
        overlay = json.loads((self.state / 'projects.compose.json').read_text())
        mount = overlay['services']['workspace']['volumes'][0]
        self.assertEqual(mount['source'], str(self.repo.resolve()).replace('$', '$$'))
        self.assertEqual(mount['target'], '/projects/delivery-a')
        self.assertFalse(mount['bind']['create_host_path'])
        self.assertEqual(overlay['services']['workspace'], overlay['services']['toolchain'])
        self.assertIn(str(self.state / 'projects.compose.json'), datacon.compose('test', 'up', root=self.root))
        self.assertEqual(overlay['secrets']['project_delivery-a']['file'], str(self.state / 'projects/delivery-a/password'))

    def test_wrong_reset_confirmation_never_reaches_database(self):
        self.add()
        with patch.object(self.manager, 'sql') as sql, self.assertRaises(projects.ProjectError):
            self.manager.provision('delivery-a', reset=True, confirmation='delivery-b')
        sql.assert_not_called()

    def test_unmanaged_database_or_role_cannot_be_reset(self):
        entry = self.add()
        marker = projects.identity(entry)[1]
        for role_marker, db_marker, owner in [('other', marker, 'postgres'), (marker, 'other', 'postgres'), (marker, marker, 'somebody')]:
            response = json.dumps({'role': {'marker': role_marker, 'safe': True}, 'database': {'marker': db_marker, 'owner': owner}})
            with self.subTest(owner=owner, db_marker=db_marker), patch.object(self.manager, 'sql', return_value=response) as sql:
                with self.assertRaises(projects.ProjectError):
                    self.manager.provision('delivery-a', reset=True, confirmation='delivery-a')
                self.assertEqual(sql.call_count, 1)
                self.assertNotIn('DROP', sql.call_args.args[0])

    def test_editor_is_generated_outside_delivery_and_targets_selected_instance(self):
        self.add()
        folder = self.manager.editor('delivery-a')
        config = json.loads((folder / '.devcontainer/devcontainer.json').read_text())
        self.assertEqual(config['workspaceFolder'], '/projects/delivery-a/nested')
        self.assertEqual(config['shutdownAction'], 'none')
        instance = json.loads((self.state / 'instance.compose.json').read_text())
        self.assertEqual(instance['name'], 'datacon-test')
        self.assertFalse((self.repo / '.devcontainer').exists())
        self.assertTrue(folder.is_relative_to(self.state))

    def test_retained_instances_without_uid_config_keep_original_ownership(self):
        (self.state / 'workspace.json').unlink()
        with patch.object(datacon.platform, 'system', return_value='Linux'), patch.object(datacon.os, 'getuid', return_value=1234):
            env = datacon.environment('test', self.root)
        self.assertEqual(env['DATACON_UID'], '1000')

    def test_new_linux_instance_records_unprivileged_host_ids(self):
        with patch.object(datacon.platform, 'system', return_value='Linux'), patch.object(datacon.os, 'getuid', return_value=1234), patch.object(datacon.os, 'getgid', return_value=4321):
            state = datacon.initialise('linux', self.root)
        self.assertEqual(json.loads((state / 'workspace.json').read_text()), {'uid': 1234, 'gid': 4321})
        self.assertEqual(datacon.environment('linux', self.root)['DATACON_UID'], '1234')


if __name__ == '__main__':
    unittest.main()
