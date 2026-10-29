#!/usr/bin/env python3
"""Check repository Markdown links without network access."""

from pathlib import Path
import re
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]


def main():
    errors = []
    paths = [*ROOT.glob('*.md'), *ROOT.glob('docs/**/*.md'), *ROOT.glob('.github/*.md')]
    for path in paths:
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', path.read_text()):
            target = target.split('#', 1)[0]
            if not target or '://' in target or target.startswith('mailto:'):
                continue
            if not (path.parent / unquote(target)).exists():
                errors.append(str(path.relative_to(ROOT)) + ': ' + target)
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print(f'Local Markdown links passed ({len(paths)} files)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
