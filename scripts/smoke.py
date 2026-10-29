#!/usr/bin/env python3
"""Run inside the workspace. SQL objects are rolled back on success or failure."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import uuid


def main():
    if os.getuid() == 0:
        raise RuntimeError("Workspace must run as a non-root user")
    with tempfile.TemporaryDirectory(prefix=".datacon-smoke-", dir="/workspaces") as directory:
        Path(directory, "write-check").write_text("writable\n")
    subprocess.run(["git", "--version"], check=True)
    subprocess.run(["python", "-m", "pip", "check"], check=True)
    env = os.environ.copy()
    env["PGPASSWORD"] = Path("/run/secrets/developer_password").read_text().strip()
    table = "smoke_" + uuid.uuid4().hex
    sql = f"""
BEGIN;
SELECT 'role=' || current_user;
SELECT 'privileged=' || (rolsuper OR rolbypassrls)::text FROM pg_roles WHERE rolname = current_user;
SELECT 'extension=' || extversion FROM pg_extension WHERE extname = 'pg_duckdb';
CREATE TABLE workspace.{table} (tenant text NOT NULL, amount integer NOT NULL);
INSERT INTO workspace.{table} VALUES ('allowed', 7), ('blocked', 99);
ALTER TABLE workspace.{table} ENABLE ROW LEVEL SECURITY;
ALTER TABLE workspace.{table} FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_filter ON workspace.{table} USING (tenant = 'allowed');
SET duckdb.force_execution = false;
SELECT 'postgres=' || sum(amount)::text FROM workspace.{table};
SET duckdb.force_execution = true;
EXPLAIN SELECT sum(amount) FROM workspace.{table};
SELECT 'duckdb=' || sum(amount)::text FROM workspace.{table};
ROLLBACK;
"""
    result = subprocess.run(["psql", "-X", "-qAt", "--set", "ON_ERROR_STOP=1"],
                            input=sql, text=True, env=env, capture_output=True, timeout=60)
    if result.returncode:
        raise RuntimeError("Database smoke query failed: " + result.stderr.strip())
    lines = result.stdout.splitlines()
    # The v1.1.1 image retains SQL extension version 1.1.0; see its
    # https://github.com/duckdb/pg_duckdb/blob/v1.1.1/pg_duckdb.control.
    required = {"role=developer", "privileged=false", "extension=1.1.0", "postgres=7", "duckdb=7"}
    if not required.issubset(lines) or not any("DuckDBScan" in line for line in lines):
        raise RuntimeError("Role/RLS/accelerated-plan assertions failed:\n" + result.stdout)
    print(json.dumps({"passed": True, "uid": os.getuid(), "extension_version": "1.1.0",
                      "rls": "forced, both execution paths",
                      "duckdb_plan_observed": True, "scope": "basic smoke only; full DC-010 qualification remains"}, indent=2))


if __name__ == "__main__":
    main()
