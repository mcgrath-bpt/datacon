"""Host-only checks for identity, offline pins and diagnostic failure boundaries."""

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import baseline
import diagnostics
import lock_toolchain


class ToolchainTests(unittest.TestCase):
    def test_vendored_schemas_match_the_pins_and_have_only_local_references(self):
        manifest = json.loads((ROOT / 'platform/schemas.json').read_text())
        def refs(value):
            if isinstance(value, dict):
                if '$ref' in value:
                    self.assertTrue(value['$ref'].startswith('#'))
                for child in value.values():
                    refs(child)
            elif isinstance(value, list):
                for child in value:
                    refs(child)
        for version, entry in manifest['schemas'].items():
            with self.subTest(version=version):
                data = (ROOT / 'platform' / entry['path']).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), entry['sha256'])
                refs(json.loads(data))

    def test_runtime_identity_changes_with_inputs_but_not_documentation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'compose.yaml').write_text('original')
            before = baseline.identity(root)['runtime_inputs_sha256']
            (root / 'README.md').write_text('documentation')
            self.assertEqual(baseline.identity(root)['runtime_inputs_sha256'], before)
            (root / 'compose.yaml').write_text('changed')
            self.assertNotEqual(baseline.identity(root)['runtime_inputs_sha256'], before)

    def test_diagnostics_do_not_create_state_or_claim_readiness_without_services(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = diagnostics.inspect(root, 'new', lambda command: None, True)
            self.assertFalse(report['ready'])
            self.assertFalse(report['baseline_matches'])
            self.assertFalse((root / '.local').exists())
            self.assertEqual(report['services']['warehouse']['status'], 'absent')

    def test_malformed_probe_is_not_readiness(self):
        self.assertEqual(diagnostics.json_probe(lambda command: 'password=secret', []), {})
        self.assertEqual(diagnostics.json_probe(lambda command: '[]', []), {})

    def test_healthy_services_with_an_old_or_wrong_image_are_unmatched(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            digest = 'sha256:' + 'a' * 64
            (root / 'compose.yaml').write_text('image: pgduckdb/pgduckdb:17@' + digest)
            fingerprint = baseline.identity(root)['runtime_inputs_sha256']
            running = {'runtime_inputs_sha256': fingerprint}
            warehouse = {'architecture': 'arm64', 'digests': ['pgduckdb/pgduckdb@' + digest]}
            def probe(command):
                if command[:2] == ['docker', 'ps']:
                    return 'a' * 12 if 'label=com.docker.compose.service=workspace' in command else 'b' * 12
                if command[:2] == ['docker', 'inspect']:
                    return json.dumps({'health': 'healthy', 'status': 'running', 'image': command[-1]})
                if command[:3] == ['docker', 'image', 'inspect']:
                    return json.dumps(warehouse if command[-1] == 'b' * 12 else {'architecture': 'arm64'})
                if command[:2] == ['docker', 'exec']:
                    return json.dumps(running)
            report = diagnostics.inspect(root, 'test', probe, True)
            self.assertTrue(report['ready'])
            self.assertTrue(report['baseline_matches'])
            running.clear()
            self.assertFalse(diagnostics.inspect(root, 'test', probe, True)['baseline_matches'])
            running['runtime_inputs_sha256'] = fingerprint
            warehouse['digests'] = ['pgduckdb/pgduckdb@sha256:' + 'b' * 64]
            self.assertFalse(diagnostics.inspect(root, 'test', probe, True)['baseline_matches'])

    def test_lock_rejects_source_distribution_and_architecture_version_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = [Path(directory) / name for name in ('arm.json', 'amd.json')]
            item = {'metadata': {'name': 'example', 'version': '1.0'}, 'download_info': {
                'url': 'https://files.pythonhosted.org/example.whl',
                'archive_info': {'hashes': {'sha256': 'a' * 64}}}}
            for path in paths:
                path.write_text(json.dumps({'install': [item]}))
            self.assertEqual(lock_toolchain.collect(paths)['example']['version'], '1.0')
            item['metadata']['version'] = '2.0'
            paths[1].write_text(json.dumps({'install': [item]}))
            with self.assertRaisesRegex(ValueError, 'version mismatch'):
                lock_toolchain.collect(paths)
            item['download_info']['url'] = 'https://files.pythonhosted.org/example.tar.gz'
            paths[0].write_text(json.dumps({'install': [item]}))
            with self.assertRaisesRegex(ValueError, 'binary wheels'):
                lock_toolchain.collect(paths)


if __name__ == '__main__':
    unittest.main()
