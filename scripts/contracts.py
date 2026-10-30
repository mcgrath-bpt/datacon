#!/usr/bin/env python3
"""Validate ODCS 3.1/3.2 JSON or YAML against hashed, offline platform schemas."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def schema_for(version, root=ROOT):
    import jsonschema
    from referencing import Registry

    versions = {'v3.1.0': '3.1.0', 'v3.2.0': '3.2.0'}
    if version not in versions:
        raise ValueError('Supported apiVersion values are v3.1.0 and v3.2.0')
    manifest = json.loads((root / 'platform/schemas.json').read_text())
    entry = manifest['schemas'][versions[version]]
    data = (root / 'platform' / entry['path']).read_bytes()
    if hashlib.sha256(data).hexdigest() != entry['sha256']:
        raise ValueError('ODCS schema integrity mismatch')
    schema = json.loads(data)
    validator = jsonschema.validators.validator_for(schema)
    validator.check_schema(schema)
    # An empty registry has no network retriever. External refs fail closed.
    return validator(schema, registry=Registry())


def validate(document):
    if not isinstance(document, dict):
        raise ValueError('Contract must be an object')
    validator = schema_for(document.get('apiVersion'))
    # Do not include data values or upstream error messages in diagnostics.
    errors = sorted({('/' + '/'.join(map(str, error.absolute_path)), str(error.validator))
                     for error in validator.iter_errors(document)})
    return {'valid': not errors, 'apiVersion': document['apiVersion'],
            'errors': [{'path': path, 'rule': rule} for path, rule in errors]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('contract', type=Path)
    args = parser.parse_args()
    try:
        if args.contract.suffix.lower() in ('.yaml', '.yml'):
            import yaml
            document = yaml.safe_load(args.contract.read_text())
        else:
            document = json.loads(args.contract.read_text())
        report = validate(document)
    except Exception as error:
        # YAML/parser exceptions can contain the full input, so expose only type.
        print(json.dumps({'valid': False, 'error': type(error).__name__,
                          'next_step': 'Check the file, supported apiVersion and platform schema hashes.'}))
        return 1
    print(json.dumps(report, indent=2))
    return 0 if report['valid'] else 1


if __name__ == '__main__':
    sys.exit(main())
