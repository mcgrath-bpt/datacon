#!/usr/bin/env python3
"""Evaluator-only pinned Opharma acceptance; never modifies an existing checkout."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import uuid

PLATFORM = Path(__file__).resolve().parents[1]


def run(command, cwd, env):
    subprocess.run(command, cwd=cwd, env=env, check=True)


def database_snapshot(database):
    with sqlite3.connect(database) as connection:
        tables = connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
        snapshot = {}
        for (table,) in tables:
            quoted = '"' + table.replace('"', '""') + '"'
            rows = connection.execute("SELECT * FROM " + quoted).fetchall()
            # Compare multisets including duplicate counts, independent of row order.
            serialised = sorted(json.dumps(row, default=str) for row in rows)
            snapshot[table] = hashlib.sha256("\n".join(serialised).encode()).hexdigest()
        return snapshot


def main():
    spec = json.loads((PLATFORM / "platform/reference.json").read_text())
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    destination = Path("/workspaces") / ("opharma-" + stamp + "-" + uuid.uuid4().hex[:8])
    # mkdir is exclusive; neither clone nor subsequent commands touch retained work.
    destination.mkdir()
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["PYTHONNOUSERSITE"] = "1"
    env["GIT_TERMINAL_PROMPT"] = "0"
    run(["git", "clone", "--no-checkout", "--filter=blob:none", "--", spec["repository"], str(destination)], Path("/workspaces"), env)
    run(["git", "fetch", "--depth=1", "origin", spec["commit"]], destination, env)
    run(["git", "checkout", "--detach", spec["commit"]], destination, env)
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=destination, env=env, text=True).strip()
    if revision != spec["commit"]:
        raise RuntimeError("Reference revision does not match the platform pin")
    project = destination / spec["subdirectory"]
    evidence = Path("/workspaces/.datacon-evidence") / destination.name
    evidence.mkdir(parents=True)
    fixture, database = evidence / "fixture", evidence / "model.sqlite"
    python = sys.executable
    run([python, "src/odcs.py"], project, env)
    # Run a small wrapper to record actual counts and skips, not prior PR claims.
    test_command = """import json, sys, unittest
suite = unittest.defaultTestLoader.discover('tests')
result = unittest.TextTestRunner(verbosity=2).run(suite)
with open(sys.argv[1], 'w') as stream:
    json.dump({'run': result.testsRun, 'skipped': len(result.skipped), 'passed': result.wasSuccessful()}, stream)
sys.exit(0 if result.wasSuccessful() else 1)
"""
    run([python, "-c", test_command, str(evidence / "tests.json")], project, env)
    tests = json.loads((evidence / "tests.json").read_text())
    if tests["run"] != spec["expected_tests"] or tests["skipped"] != spec["expected_skipped_tests"]:
        raise RuntimeError("Test/skip counts differ from the pinned reference; inspect before accepting")
    command = [python, "src/run_operations.py", "--data", str(fixture), "--db", str(database)]
    run(command, project, env)
    report_file = fixture / "evidence/operations-report.json"
    initial_report = json.loads(report_file.read_text())
    (evidence / "first-run.json").write_text(json.dumps(initial_report, indent=2) + "\n")
    validate_report(initial_report, spec["expected_checkpoints"])
    before = database_snapshot(database)
    run(command, project, env)
    report = json.loads(report_file.read_text())
    (evidence / "replay.json").write_text(json.dumps(report, indent=2) + "\n")
    validate_report(report, spec["expected_checkpoints"])
    if database_snapshot(database) != before:
        raise RuntimeError("Identical replay changed stored table rows")
    hashes = {}
    for label, base in (("contracts", project / "contracts"), ("public_s3", fixture / "public_s3")):
        for path in sorted(base.rglob("*")):
            if path.is_file():
                hashes[label + "/" + str(path.relative_to(base))] = hashlib.sha256(path.read_bytes()).hexdigest()
    summary = {"recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "reference_commit": revision, "python": sys.version, "tests": tests,
               "checkpoints": len(report["checkpoints"]), "identical_replay": True,
               "file_sha256": hashes, "snowflake": "NOT_EXECUTED", "passed": True}
    (evidence / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"passed": True, "checkout": str(destination), "evidence": str(evidence)}, indent=2))


def validate_report(report, expected):
    if not report["passed"] or len(report["checkpoints"]) != expected:
        raise RuntimeError("Reference checkpoint acceptance failed")


if __name__ == "__main__":
    main()
