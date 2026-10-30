#!/usr/bin/env python3
"""Prepare reviewed wheel locks from two pip reports; never run during installation."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen


def collect(reports):
    packages = {}
    inventories = []
    for report in reports:
        inventory = {}
        for item in json.loads(report.read_text())['install']:
            name = item['metadata']['name'].lower().replace('_', '-').replace('.', '-')
            version = item['metadata']['version']
            inventory[name] = version
            info = item['download_info']
            url = info['url']
            if urlparse(url).hostname != 'files.pythonhosted.org' or not url.endswith('.whl'):
                raise ValueError('Only PyPI binary wheels may enter this lock')
            package = packages.setdefault(name, {'version': version, 'wheels': {}})
            if package['version'] != version:
                raise ValueError('Architecture version mismatch: ' + name)
            package['wheels'][url] = info['archive_info']['hashes']['sha256']
        inventories.append(inventory)
    if inventories[0] != inventories[1]:
        raise ValueError('Architecture dependency sets differ')
    return packages


def verify_wheel(item):
    url, expected = item
    digest = hashlib.sha256()
    with urlopen(url, timeout=120) as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    if digest.hexdigest() != expected:
        raise ValueError('Downloaded wheel hash mismatch: ' + url)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reports', nargs=2, type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    packages = collect(args.reports)
    wheels = sorted({item for package in packages.values() for item in package['wheels'].items()})
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(verify_wheel, wheels))
    args.output.mkdir(parents=True, exist_ok=True)
    lines = ['# Binary-only CPython 3.14 Linux ARM64/AMD64 lock. See TOOLCHAIN.md.']
    provenance = {}
    for name, package in sorted(packages.items()):
        lines.append(name + '==' + package['version'] + ' ' + ' '.join(
            '--hash=sha256:' + digest for digest in sorted(set(package['wheels'].values()))))
        provenance[name] = {'version': package['version'], 'wheels': [
            {'filename': url.rsplit('/', 1)[-1], 'url': url, 'sha256': digest}
            for url, digest in sorted(package['wheels'].items())]}
    (args.output / 'toolchain.txt').write_text('\n'.join(lines) + '\n')
    (args.output / 'toolchain-wheels.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print(f'Verified {len(wheels)} wheel downloads for {len(packages)} pinned packages')


if __name__ == '__main__':
    main()
