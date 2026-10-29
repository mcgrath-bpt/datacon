#!/usr/bin/env python3
"""Select a delivery's working directory and credentials without shell evaluation."""

import argparse
import os
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', required=True)
    parser.add_argument('--password-file', type=Path, required=True)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--workdir', required=True)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        parser.error('provide a command')
    root = args.repository.resolve(strict=True)
    directory = (root / args.workdir).resolve(strict=True)
    if not directory.is_relative_to(root):
        parser.error('working directory escapes the repository')
    env = os.environ.copy()
    for key in ('PGSERVICE', 'PGSERVICEFILE', 'PGOPTIONS', 'PGPASSFILE', 'DATABASE_URL'):
        env.pop(key, None)
    env.update(PGHOST='warehouse', PGPORT='5432', PGDATABASE=args.database, PGUSER=args.database,
               PGPASSWORD=args.password_file.read_text().strip(), PGCONNECT_TIMEOUT='10')
    os.chdir(directory)
    os.execvpe(command[0], command, env)


if __name__ == '__main__':
    sys.exit(main())
