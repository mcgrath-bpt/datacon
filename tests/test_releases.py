"""Exercise release trust boundaries using real independent Git checkouts."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import releases
import repository_rules


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='datacon release ')
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name) / 'platform checkout'
        self.root.mkdir()
        (self.root / 'platform').mkdir()
        (self.root / 'compose.yaml').write_text('fixture runtime\n')
        (self.root / 'evidence.md').write_text('Fixture only; not native evidence.\n')
        (self.root / '.gitignore').write_text('.local/\n')
        shutil.copyfile(ROOT / 'platform/release-policy.json', self.root / 'platform/release-policy.json')
        self.write(self.root / 'platform/capabilities.json', {'schema_version': 1, 'capabilities': {
            'test-tool': {'status': 'qualified', 'provision': ['compose.yaml'],
                          'targets': ['local-linux-arm64'], 'evidence': ['evidence.md']}}})
        self.git('init', '--quiet')
        self.git('add', '.')
        self.commit('Fixture platform')
        self.manifest_path = Path(self.directory.name) / 'datacon-release.json'
        self.manifest = releases.candidate(self.root, '0.1.0-rc.1')
        self.write(self.manifest_path, self.manifest)
        self.pin_path = Path(self.directory.name) / 'datacon.lock.json'
        self.pin = {'schema_version': 1, 'repository': releases.REPOSITORY,
                    'release': 'v0.1.0-rc.1', 'commit': self.manifest['source']['commit'],
                    'manifest_sha256': hashlib.sha256(self.manifest_path.read_bytes()).hexdigest(),
                    'capabilities': ['test-tool'], 'target': 'local-linux-arm64'}
        self.write(self.pin_path, self.pin)

    def write(self, path, value):
        path.write_text(json.dumps(value, sort_keys=True) + '\n')

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args], text=True).strip()

    def commit(self, message):
        self.git('-c', 'user.name=Datacon test', '-c', 'user.email=test@example.invalid',
                 '-c', 'commit.gpgsign=false', 'commit', '--quiet', '-m', message)

    def verify(self, offline=True):
        return releases.verify(self.root, self.manifest_path, self.pin_path, offline=offline)

    def test_committed_candidate_is_deterministic_and_offline_is_not_approval(self):
        self.assertEqual(self.manifest, releases.candidate(self.root, '0.1.0-rc.1'))
        report = self.verify()
        self.assertEqual(report['status'], 'CONTENT_ONLY')
        self.assertIn('not inferred', report['delivery_approval'])

    def test_dirty_and_untracked_work_are_rejected_without_deletion(self):
        path = self.root / 'personal.py'
        path.write_text('retained')
        with self.assertRaisesRegex(releases.ReleaseError, 'clean committed'):
            self.verify()
        self.assertEqual(path.read_text(), 'retained')
        path.unlink()
        (self.root / 'compose.yaml').write_text('uncommitted runtime')
        with self.assertRaisesRegex(releases.ReleaseError, 'clean committed'):
            self.verify()

    def test_ignored_runtime_input_cannot_hide_from_candidate(self):
        (self.root / '.gitignore').write_text('.local/\n/scripts/personal.py\n')
        self.git('add', '.gitignore')
        self.commit('Ignore experimental overlay')
        (self.root / 'scripts').mkdir()
        (self.root / 'scripts/personal.py').write_text('personal tool')
        with self.assertRaisesRegex(releases.ReleaseError, 'ignored or untracked'):
            releases.candidate(self.root, '0.1.0')

    def test_manifest_tampering_is_rejected(self):
        self.manifest['source']['commit'] = 'a' * 40
        self.write(self.manifest_path, self.manifest)
        with self.assertRaisesRegex(releases.ReleaseError, 'SHA-256'):
            self.verify()

    def test_core_preview_cannot_be_labelled_v1(self):
        with self.assertRaisesRegex(releases.ReleaseError, 'full platform'):
            releases.candidate(self.root, '1.0.0')

    def test_new_platform_commit_requires_a_new_reviewed_pin(self):
        (self.root / 'compose.yaml').write_text('new committed runtime')
        self.git('add', 'compose.yaml')
        self.commit('Change baseline')
        with self.assertRaisesRegex(releases.ReleaseError, 'differs from the release manifest'):
            self.verify()

    def test_unapproved_node_capability_and_native_snowflake_target_are_rejected(self):
        for change in ({'capabilities': ['node-npm']}, {'target': 'native-snowflake'}):
            with self.subTest(change=change):
                self.write(self.pin_path, self.pin | change)
                with self.assertRaisesRegex(releases.ReleaseError, 'unavailable'):
                    self.verify()

    def test_empty_or_duplicate_capabilities_do_not_bypass_target_checks(self):
        for selection in ([], ['test-tool', 'test-tool'], 'test-tool'):
            self.write(self.pin_path, self.pin | {'capabilities': selection})
            with self.assertRaisesRegex(releases.ReleaseError, 'unique approved capability'):
                self.verify()

    def online(self, *, immutable=True, draft=False, tag_commit=None, attestation_failure=False):
        original = releases.command
        def run(args, root):
            if args[0] == 'git':
                return original(args, root)
            if args[:3] == ['gh', 'release', 'verify-asset']:
                if attestation_failure:
                    raise releases.ReleaseError('Fixture invalid attestation')
                return '{}'
            if '/releases/tags/' in args[2]:
                return json.dumps({'draft': draft, 'immutable': immutable, 'tag_name': self.pin['release']})
            if '/git/ref/tags/' in args[2]:
                return json.dumps({'object': {'type': 'commit', 'sha': tag_commit or self.pin['commit']}})
            raise AssertionError(args)
        return patch.object(releases, 'command', side_effect=run)

    def test_online_verification_requires_immutable_publication_and_valid_attestation(self):
        with self.online():
            self.assertEqual(self.verify(False)['status'], 'PUBLISHED_RELEASE_VERIFIED')
        for options in ({'immutable': False}, {'draft': True}, {'attestation_failure': True}, {'tag_commit': 'b' * 40}):
            with self.subTest(options=options), self.online(**options), self.assertRaises(releases.ReleaseError):
                self.verify(False)

    def test_catalogue_cannot_reference_missing_or_external_provision(self):
        data = json.loads((self.root / 'platform/capabilities.json').read_text())
        for entry in ('missing', '../datacon-release.json'):
            data['capabilities']['test-tool']['provision'] = [entry]
            self.write(self.root / 'platform/capabilities.json', data)
            with self.assertRaisesRegex(releases.ReleaseError, 'missing or escapes'):
                releases.catalogue(self.root)

    def test_rule_audit_rejects_missing_checks_and_bypass_actors(self):
        expected = json.loads((ROOT / 'governance/github-main.json').read_text())
        actual = json.loads(json.dumps(expected))
        actual['id'] = 123
        self.assertTrue(repository_rules.matches(actual, expected))
        actual['bypass_actors'] = [{'actor_type': 'RepositoryRole', 'actor_id': 5, 'bypass_mode': 'always'}]
        self.assertFalse(repository_rules.matches(actual, expected))
        actual['bypass_actors'] = []
        actual['rules'][-1]['parameters']['required_status_checks'].pop()
        self.assertFalse(repository_rules.matches(actual, expected))


if __name__ == '__main__':
    unittest.main()
