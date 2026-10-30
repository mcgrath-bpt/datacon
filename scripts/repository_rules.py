#!/usr/bin/env python3
"""Audit or explicitly apply the checked-in GitHub repository rules.

Administrative host tool; requires gh with repository administration permission.
The Tech Lead review rules are separate because a second account is still pending.
"""

import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = 'mcgrath-bpt/datacon'


def api(path, method='GET', payload=None):
    command = ['gh', 'api', 'repos/' + REPOSITORY + '/' + path, '--method', method]
    if payload is not None:
        command += ['--input', '-']
    result = subprocess.run(command, input=json.dumps(payload) if payload is not None else None,
                            text=True, capture_output=True, timeout=60)
    if result.returncode:
        raise ValueError('GitHub ' + method + ' failed for ' + path + '; check administration access.')
    return json.loads(result.stdout) if result.stdout.strip() else None


def matches(actual, expected):
    # GitHub may add response defaults within parameters. Compare every declared
    # field, and require the same rules so an omitted gate cannot pass an audit.
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(k in actual and matches(actual[k], v) for k, v in expected.items())
    if isinstance(expected, list):
        return isinstance(actual, list) and len(actual) == len(expected) and all(
            any(matches(a, e) for a in actual) for e in expected)
    return actual == expected


def sync(template, apply=False):
    expected = json.loads((ROOT / 'governance' / template).read_text())
    found = [entry for entry in api('rulesets?per_page=100') if entry['name'] == expected['name']]
    if len(found) > 1:
        raise ValueError('Duplicate named rulesets; inspect them without deleting existing policy.')
    if apply:
        endpoint = 'rulesets/' + str(found[0]['id']) if found else 'rulesets'
        api(endpoint, 'PUT' if found else 'POST', expected)
        found = [entry for entry in api('rulesets?per_page=100') if entry['name'] == expected['name']]
    actual = api('rulesets/' + str(found[0]['id'])) if found else {}
    return {'name': expected['name'], 'matches': matches(actual, expected),
            'id': actual.get('id'), 'url': actual.get('_links', {}).get('html', {}).get('href')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Apply required CI checks and enable immutable releases')
    parser.add_argument('--activate-review', action='store_true', help='Also apply owner review after reviewer onboarding')
    args = parser.parse_args()
    if args.activate_review and not args.apply:
        parser.error('--activate-review requires --apply; use the normal audit to inspect both rulesets')
    try:
        if args.activate_review:
            collaborators = api('collaborators?per_page=100')
            if sum(bool(x.get('permissions', {}).get('push')) for x in collaborators) < 2:
                raise ValueError('Reviewer activation requires at least two collaborators with write permission.')
            errors = api('codeowners/errors')
            if errors.get('errors'):
                raise ValueError('Resolve CODEOWNERS errors on the default branch before activation.')
            content = api('contents/.github/CODEOWNERS')
            owners = set()
            for line in base64.b64decode(content['content']).decode().splitlines():
                fields = line.split('#', 1)[0].split()
                if fields and fields[0] == '*':
                    owners = {field.removeprefix('@') for field in fields[1:]}
            writers = {x['login'] for x in collaborators if x.get('permissions', {}).get('push')}
            if len(owners & writers) < 2:
                raise ValueError('Add both authorised write-capable accounts to the default CODEOWNERS rule first.')
        reports = [sync('github-main.json', args.apply), sync('github-review.json', args.activate_review)]
        if args.apply:
            api('immutable-releases', 'PUT')
        immutable = api('immutable-releases')
        report = {'repository': REPOSITORY, 'rulesets': reports,
                  'immutable_releases': immutable.get('enabled') is True,
                  'review_enforced': reports[1]['matches']}
        print(json.dumps(report, indent=2))
        return 0 if all(r['matches'] for r in reports) and report['immutable_releases'] else 1
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        print('repository rules: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
