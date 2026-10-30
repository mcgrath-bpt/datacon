"""Content-bound release candidates and independently pinned delivery adoption.

No command publishes a release, installs a dependency or modifies a delivery.
GitHub CLI is needed only for online verification of an immutable release asset.
"""

import hashlib
import json
from pathlib import Path
import re
import subprocess

import baseline

REPOSITORY = 'mcgrath-bpt/datacon'
VERSION = re.compile(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-rc\.[1-9][0-9]*)?\Z')


class ReleaseError(ValueError):
    pass


def command(arguments, root):
    result = subprocess.run(arguments, cwd=root, text=True, capture_output=True, timeout=60)
    if result.returncode:
        raise ReleaseError('Release verification command failed: ' + arguments[0] + '; check access and prerequisites.')
    return result.stdout.strip()


def git(root, *arguments):
    return command(['git', '-C', str(root), *arguments], root)


def catalogue(root):
    value = json.loads((root / 'platform/capabilities.json').read_text())
    if value.get('schema_version') != 1 or not isinstance(value.get('capabilities'), dict) or not value['capabilities']:
        raise ReleaseError('Invalid capability catalogue.')
    for name, item in value['capabilities'].items():
        if not re.fullmatch(r'[a-z][a-z0-9-]*', name) or item.get('status') != 'qualified':
            raise ReleaseError('Only explicitly qualified capabilities belong in a release.')
        for key in ('provision', 'evidence', 'targets'):
            if not isinstance(item.get(key), list) or not item[key] or not all(isinstance(p, str) for p in item[key]):
                raise ReleaseError('Missing capability ' + key + ': ' + name)
        for entry in item['provision'] + item['evidence']:
            path = root / entry
            if not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
                raise ReleaseError('Capability path is missing or escapes the repository: ' + entry)
    return value


def source(root):
    if git(root, 'status', '--porcelain', '--untracked-files=all'):
        raise ReleaseError('Use a clean committed checkout; retained work has not been changed.')
    inputs = baseline.identity(root)
    tracked = set(git(root, 'ls-files', '-z').split('\0'))
    if set(inputs['inputs']) - tracked:
        raise ReleaseError('Runtime inputs include ignored or untracked files.')
    return {
        'commit': git(root, 'rev-parse', 'HEAD'),
        'tree': git(root, 'rev-parse', 'HEAD^{tree}'),
        'runtime_inputs_sha256': inputs['runtime_inputs_sha256'],
        'inputs': inputs['inputs'],
    }


def candidate(root, version):
    if not VERSION.fullmatch(version):
        raise ReleaseError('Use an exact MAJOR.MINOR.PATCH version, optionally followed by -rc.N.')
    policy = json.loads((root / 'platform/release-policy.json').read_text())
    if policy.get('schema_version') != 1 or policy.get('repository') != REPOSITORY:
        raise ReleaseError('Invalid release policy.')
    if int(version.split('.')[0]) >= 1 and policy.get('scope') != 'full-platform':
        raise ReleaseError('Version 1 and later require the qualified full platform, including OpenMetadata.')
    return {'schema_version': 1, 'repository': REPOSITORY, 'version': version, 'tag': 'v' + version,
            'source': source(root), 'catalogue': catalogue(root),
            'scope': policy['scope'], 'host_evidence': policy['host_evidence'],
            'limitations': policy['limitations']}


def verify(root, manifest_path, pin_path, *, offline=False):
    raw = manifest_path.read_bytes()
    manifest, pin = json.loads(raw), json.loads(pin_path.read_text())
    if not isinstance(manifest, dict) or not isinstance(pin, dict) or not isinstance(manifest.get('source'), dict):
        raise ReleaseError('Manifest and pin must be objects with a valid source identity.')
    if pin.get('schema_version') != 1 or pin.get('repository') != REPOSITORY:
        raise ReleaseError('Delivery pin must name the canonical Datacon repository and schema version 1.')
    if pin.get('manifest_sha256') != hashlib.sha256(raw).hexdigest():
        raise ReleaseError('Release manifest SHA-256 differs from the reviewed delivery pin.')
    if manifest.get('schema_version') != 1 or manifest.get('repository') != REPOSITORY:
        raise ReleaseError('Invalid release manifest.')
    version = manifest.get('version', '')
    if not isinstance(version, str) or not VERSION.fullmatch(version) or manifest.get('tag') != 'v' + version:
        raise ReleaseError('Invalid release version/tag.')
    if pin.get('release') != manifest['tag'] or pin.get('commit') != manifest.get('source', {}).get('commit'):
        raise ReleaseError('Release or commit differs from the reviewed delivery pin.')
    if manifest != candidate(root, version):
        raise ReleaseError('Checkout content, capability catalogue or release policy differs from the release manifest.')
    selected = pin.get('capabilities')
    if not isinstance(selected, list) or not selected or not all(isinstance(x, str) for x in selected) or len(set(selected)) != len(selected):
        raise ReleaseError('Select at least one unique approved capability.')
    for name in selected:
        item = manifest['catalogue']['capabilities'].get(name)
        if not item or pin.get('target') not in item['targets']:
            raise ReleaseError('Capability is unavailable for the requested target: ' + name)
    if not offline:
        release = json.loads(command(['gh', 'api', 'repos/' + REPOSITORY + '/releases/tags/' + manifest['tag']], root))
        if release.get('draft') is not False or release.get('immutable') is not True or release.get('tag_name') != manifest['tag']:
            raise ReleaseError('Delivery adoption requires a published immutable GitHub release.')
        # Verify the local bytes against GitHub's signed release attestation.
        command(['gh', 'release', 'verify-asset', manifest['tag'], str(manifest_path.resolve()), '--repo', REPOSITORY], root)
        reference = json.loads(command(['gh', 'api', 'repos/' + REPOSITORY + '/git/ref/tags/' + manifest['tag']], root))['object']
        for _ in range(8):
            if reference.get('type') == 'commit':
                break
            if reference.get('type') != 'tag' or not re.fullmatch('[a-f0-9]{40}', reference.get('sha', '')):
                raise ReleaseError('Invalid published tag target.')
            reference = json.loads(command(['gh', 'api', 'repos/' + REPOSITORY + '/git/tags/' + reference['sha']], root))['object']
        if reference.get('type') != 'commit' or reference.get('sha') != pin['commit']:
            raise ReleaseError('Published release tag does not identify the pinned platform commit.')
    return {'release': pin['release'], 'commit': pin['commit'], 'capabilities': selected,
            'target': pin['target'], 'status': 'CONTENT_ONLY' if offline else 'PUBLISHED_RELEASE_VERIFIED',
            'delivery_approval': 'Required through the delivery repository review controls; not inferred by this command.'}


def add_parser(commands):
    release = commands.add_parser('release', help='Prepare and verify immutable-release inputs without publishing')
    actions = release.add_subparsers(dest='release_action', required=True)
    actions.add_parser('catalogue', help='Validate and print the qualified capability catalogue')
    prepare = actions.add_parser('candidate', help='Prepare a manifest from a clean committed checkout')
    prepare.add_argument('--version', required=True)
    prepare.add_argument('--output', required=True, type=Path)
    check = actions.add_parser('verify', help='Verify a delivery pin and GitHub release attestation')
    check.add_argument('--manifest', required=True, type=Path)
    check.add_argument('--pin', required=True, type=Path)
    check.add_argument('--offline', action='store_true', help='Check content only; does not establish publication or approval')


def handle(args, root):
    if args.release_action == 'catalogue':
        report = catalogue(root)
    elif args.release_action == 'candidate':
        report = candidate(root, args.version)
        # Refuse to overwrite an existing candidate or alter a tracked file.
        with args.output.open('x') as stream:
            stream.write(json.dumps(report, indent=2, sort_keys=True) + '\n')
        print('Candidate prepared; publication and Tech Lead approval remain required.')
        return 0
    else:
        report = verify(root, args.manifest, args.pin, offline=args.offline)
    print(json.dumps(report, indent=2))
    return 0
