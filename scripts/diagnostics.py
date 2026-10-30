"""Read-only, allow-listed diagnostics. Never emit Docker environment or raw errors."""

import json
import os
from pathlib import Path
import re
import shutil

from baseline import identity

ARCHITECTURES = {'arm64': 'arm64', 'aarch64': 'arm64', 'amd64': 'amd64', 'x86_64': 'amd64'}


def json_probe(probe, command):
    try:
        value = json.loads(probe(command) or 'null')
        return value if isinstance(value, dict) else {}
    except (ValueError, TypeError):
        return {}


def inspect(root, instance, probe, daemon_available):
    state = root / '.local/instances' / instance
    baseline = identity(root)
    baseline['working_tree_dirty'] = bool(probe(['git', '-C', str(root), 'status', '--porcelain']))
    nearest = state
    while not nearest.exists() and nearest != nearest.parent:
        nearest = nearest.parent
    result = {'baseline': baseline, 'paths': {'repository': str(root), 'state': str(state),
              'state_exists': state.is_dir(), 'state_parent_writable': os.access(nearest, os.W_OK),
              'host_free_bytes': shutil.disk_usage(nearest).free,
              'credentials_complete': all((state / name).is_file() and (state / name).stat().st_size > 0
                                          for name in ('developer_password', 'postgres_password'))},
              'services': {}, 'ready': False}
    if not daemon_available:
        return result
    for service in ('workspace', 'warehouse'):
        ids = probe(['docker', 'ps', '--all', '--filter', 'label=com.docker.compose.project=datacon-' + instance,
                     '--filter', 'label=com.docker.compose.service=' + service,
                     '--filter', 'label=com.docker.compose.oneoff=False', '--format', '{{.ID}}']) or ''
        if not re.fullmatch('[a-f0-9]{12,64}', ids):
            result['services'][service] = {'status': 'absent' if not ids else 'ambiguous'}
            continue
        details = json_probe(probe, ['docker', 'inspect', '--format',
            '{"status":{{json .State.Status}},"health":{{if .State.Health}}{{json .State.Health.Status}}{{else}}null{{end}},'
            '"image":{{json .Image}},"memory_limit_bytes":{{json .HostConfig.Memory}},'
            '"cpu_limit_nanocpus":{{json .HostConfig.NanoCpus}},"restart":{{json .HostConfig.RestartPolicy.Name}}}', ids])
        if details.get('image'):
            details.update(json_probe(probe, ['docker', 'image', 'inspect', '--format',
                '{"architecture":{{json .Architecture}},"digests":{{json .RepoDigests}}}', details['image']]))
        if service == 'warehouse':
            expected = re.search(r'image: (pgduckdb/pgduckdb):[^@\s]+@(sha256:[a-f0-9]{64})',
                                 (root / 'compose.yaml').read_text())
            details['matches_checkout'] = bool(expected and
                expected[1] + '@' + expected[2] in (details.get('digests') or []))
        if service == 'workspace' and details.get('status') == 'running':
            running = json_probe(probe, ['docker', 'exec', ids, 'cat', '/opt/datacon/baseline.json'])
            digest = running.get('runtime_inputs_sha256')
            details['runtime_inputs_sha256'] = digest
            details['matches_checkout'] = bool(digest and digest == baseline['runtime_inputs_sha256'])
        result['services'][service] = details or {'status': 'inspection_failed'}
    result['ready'] = all(result['services'].get(service, {}).get('health') == 'healthy'
                          and result['services'][service].get('status') == 'running'
                          for service in ('workspace', 'warehouse'))
    result['baseline_matches'] = all(result['services'][service].get('matches_checkout', False)
                                     for service in ('workspace', 'warehouse'))
    return result
