#!/usr/bin/env python3
"""Identify runtime inputs independently of documentation and mutable Git refs."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = ('.devcontainer/Dockerfile', 'containers/toolchain/Dockerfile', 'containers/postgres/*.sh',
            '.python-version', 'datacon', 'compose.yaml',
            'requirements/**/*.txt', 'requirements/os/*', 'scripts/*.py', 'platform/**/*.json')


def identity(root=ROOT):
    paths = sorted({path for pattern in PATTERNS for path in root.glob(pattern) if path.is_file()})
    inputs = {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    digest = hashlib.sha256(json.dumps(inputs, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'runtime_inputs_sha256': digest, 'inputs': inputs,
            'release': None, 'release_status': 'development; no approved immutable release published'}


if __name__ == '__main__':
    print(json.dumps(identity(), indent=2))
