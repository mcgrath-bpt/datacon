"""Integrity and evidence boundaries; real builds exercise the native gates."""

from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import qualify
import verify_os


class LockTests(unittest.TestCase):
    def test_os_inventory_detects_changes_additions_and_removals(self):
        approved = 'git\t1:2.39.5\tarm64\n'
        verify_os.verify(approved, approved)
        for actual in ('', approved + 'extra\t1\tall\n', approved.replace('2.39.5', '2.40.0')):
            with self.subTest(actual=actual), self.assertRaisesRegex(ValueError, 'OS inventory mismatch'):
                verify_os.verify(approved, actual)

    def test_native_gate_rejects_emulation_and_unexpected_runners(self):
        self.assertEqual(qualify.assert_native('aarch64', 'arm64'), 'arm64')
        self.assertEqual(qualify.assert_native('x86_64', 'x86_64', 'amd64'), 'amd64')
        for values in [('arm64', 'amd64', None), ('x86_64', 'amd64', 'arm64'), ('unknown', 'unknown', None)]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                qualify.assert_native(*values)

    def test_repeat_comparison_rejects_dependency_drift(self):
        qualify.compare_inventories({'packages': ['a']}, {'packages': ['a']})
        with self.assertRaisesRegex(ValueError, 'different dependency inventories'):
            qualify.compare_inventories({'packages': ['a']}, {'packages': ['b']})


class EvidenceTests(unittest.TestCase):
    def test_redacts_instance_secrets_and_authenticated_urls(self):
        raw = 'private-password https://user:secret@example.com/index token=private-token'
        redacted = qualify.sanitise(raw, ['private-password'])
        for secret in ('private-password', 'user:secret', 'private-token'):
            self.assertNotIn(secret, redacted)
        self.assertIn('example.com/index', redacted)

    def test_expected_failure_must_match_the_integrity_error(self):
        import subprocess
        with tempfile.TemporaryDirectory() as directory:
            runner = qualify.Qualification(Path(directory), 'test')
            for code, output in [(0, 'OS inventory mismatch'), (1, 'network unavailable')]:
                with self.subTest(code=code), patch.object(qualify.subprocess, 'run', return_value=
                        subprocess.CompletedProcess([], code, output, '')):
                    with self.assertRaisesRegex(RuntimeError, 'expected integrity error'):
                        runner.run('failure', ['test'], expected_failure='OS inventory mismatch')
            with patch.object(qualify.subprocess, 'run', return_value=
                    subprocess.CompletedProcess([], 1, 'OS inventory mismatch', '')):
                runner.run('failure', ['test'], expected_failure='OS inventory mismatch')

    def test_reference_collection_cannot_copy_database_or_fixture(self):
        self.assertEqual(set(qualify.REFERENCE_FILES), {'tests.json', 'first-run.json', 'replay.json', 'summary.json'})

    def test_failure_before_ownership_does_not_stop_retained_instances(self):
        with tempfile.TemporaryDirectory() as directory:
            runner = qualify.Qualification(Path(directory), 'retained')
            with patch.object(runner, 'run', side_effect=RuntimeError('preflight failed')), patch.object(runner, 'cli') as cli:
                self.assertEqual(runner.execute(), 1)
            cli.assert_not_called()
            self.assertFalse(runner.summary['passed'])


if __name__ == '__main__':
    unittest.main()
