#!/usr/bin/env python3
"""Compare every installed Debian package with the reviewed architecture lock."""

import argparse
import difflib
from pathlib import Path
import subprocess
import sys


def inventory():
    output = subprocess.check_output([
        "dpkg-query", "-W",
        "-f=${binary:Package}\t${Version}\t${Architecture}\t${db:Status-Status}\n",
    ], text=True)
    return "".join(sorted(line.rsplit("\t", 1)[0] + "\n"
                          for line in output.splitlines() if line.endswith("\tinstalled")))


def verify(expected, actual):
    if expected != actual:
        difference = "".join(difflib.unified_diff(
            expected.splitlines(keepends=True), actual.splitlines(keepends=True),
            fromfile="approved OS inventory", tofile="installed OS inventory"))
        raise ValueError("OS inventory mismatch; review the lock refresh, do not bypass it.\n" + difference)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", action="store_true", help="Print a candidate; never approve it automatically")
    parser.add_argument("--locks", type=Path, default=Path("/opt/datacon/requirements/os"))
    args = parser.parse_args()
    actual = inventory()
    if args.inventory:
        print(actual, end="")
        return 0
    architecture = subprocess.check_output(["dpkg", "--print-architecture"], text=True).strip()
    lock = args.locks / ("bookworm-" + architecture + ".tsv")
    try:
        verify(lock.read_text(), actual)
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print("OS inventory matches " + lock.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
