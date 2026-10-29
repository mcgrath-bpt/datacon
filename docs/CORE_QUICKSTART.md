# First core increment

Updated: 2026-10-29. This core increment implements parts of DC-002/DC-003/DC-007 and completes DC-008's local reference acceptance. Host tests, Compose validation, ARM64 build/smoke, Opharma acceptance and retained/fresh lifecycle checks have passed. WSL, AMD64 and resource-envelope certification remain outstanding. It is not the complete v1 release: OpenMetadata, GX integration and native Snowflake execution remain on the backlog.

## Prerequisites

Use macOS or Linux, including the Linux side of WSL 2. The host needs Git, stable Python 3.12 or later, Docker and a Compose plugin supporting `up --wait`. Start Docker Desktop/the Docker daemon and ensure the terminal can access it. Windows acceptance must separately exercise WSL package 3.0.3.

The container targets Python 3.15.2, the latest stable release verified on 2026-10-29. The shell launcher tries installed `python3.15`, `python3.14`, `python3.13`, `python3.12`, then a qualifying `python3`; it rejects pre-releases and versions below 3.12. Set `DATACON_PYTHON` to an executable path for an explicit choice. Editor initialisation uses this same selector. On the current Mac, it selects installed Python 3.14.8; it does not replace Apple's Python or install host packages. `.python-version` records the desired development version for compatible version managers.

Allocate two CPUs and 4 GiB to Docker for the intended core measurement. The workspace is capped at 768 MiB and the warehouse at 1536 MiB; these limits leave headroom for the VM and do not establish that the target workload fits. Running additional instances increases total consumption.

Run commands below from the Datacon checkout. No host Python packages are required for the launcher or its tests.

```sh
./datacon check
./datacon config
./datacon doctor
./datacon up
./datacon smoke
./datacon reference
./datacon shell
```

`check` runs host unit tests. `config` validates Compose without a daemon. `doctor` reports the selected host interpreter, workspace target and Docker status, distinguishing denied access from an unreachable daemon without exposing raw credential-bearing errors. `up` creates local credentials once, builds the candidate workspace and waits for workspace/warehouse readiness. Build and reference checkout require network access to package/image registries and GitHub.

`smoke` verifies a non-root workspace, dependency consistency, a non-superuser database role, forced RLS under PostgreSQL and DuckDB execution, and an actual DuckDB query plan. Its test table is rolled back. This is a small acceptance case; concurrent execution, cancellation and the fuller DC-010 access matrix remain work.

`reference` creates a new independent Git checkout under `/workspaces/opharma-<timestamp>-<suffix>` at the reviewed commit. It validates ODCS, requires the recorded 35 tests with one skip, generates a new fixture, runs 14 checkpoints and checks that identical replay preserves every table's row multiset. Different counts fail visibly. It saves evidence under `/workspaces/.datacon-evidence/<checkout-name>/`, including actual test counts, contract/fixture hashes and the reference revision. Failed runs retain their checkout and any evidence already written. This is an evaluator workflow containing expected answers; it is unsuitable as an isolated agent-builder workspace.

## Develop in an independent repository

Inside `./datacon shell`, clone/open your project in `/workspaces`. Configure your own Git identity and credentials for commits/pushes. Datacon does not mount your whole host home or its Docker socket. The reference checkout starts at a detached commit; create a project feature branch before making delivery changes.

The workspace contains Python, Git, SSH client, Make, `psql` and the pinned JSON Schema dependency set. Platform tools and guidance are available under `/opt/datacon`. Personal tools can be installed into user-owned environments. Reproducible delivery dependencies still require the platform/Tech Lead process.

For SQL, use the configured `PGHOST`, `PGDATABASE` and `PGUSER`. Only the developer credential is mounted in the workspace. Supply it to an individual `psql` process when needed:

```sh
PGPASSWORD="$(cat /run/secrets/developer_password)" psql
```

The warehouse exposes no host port. Each instance currently has one developer role and the `workspace` schema. Separate projects needing isolated database identities should use separate named instances in this increment; automated per-project database/role provisioning remains DC-003 work. Several Git repositories can coexist in the same workspace, each retaining its own Git history and remote.

## Retain work or start fresh

```sh
./datacon down
./datacon up
./datacon fresh delivery-002
./datacon --instance delivery-002 shell
./datacon --instance delivery-002 down
```

`down` removes only the selected instance's containers/network and preserves named volumes. `up` resumes those volumes and credentials. `fresh` requires an unused name and creates separate workspace, home and database volumes; it refuses existing state or Docker resources. It never deletes the retained instance. A new instance is not yet full clean acceptance of a released baseline: immutable platform releases and CI enforcement remain outstanding.

Project checkouts live in the `workspaces` volume; personal home state lives in `developer-home`; database files live in `warehouse-data`. Names are scoped by the Compose project `datacon-<instance>`. No reset or prune command is supplied. Never use `docker compose down --volumes` for routine shutdown.

Local passwords are generated under ignored `.local/instances/<instance>/`. Their parent directory is owner-only (`0700`); individual files are read-only (`0444`) so Compose bind-mounted secrets can be read by the non-root container users. Preserve this directory with the instance's volumes. Missing credentials are an error, not an automatic password rotation. If the local state has been lost while Docker volumes remain, restore credentials before resuming; do not recreate arbitrary passwords for an existing database.

To use only the workspace for a new instance:

```sh
./datacon --instance editing up --workspace-only
```

This selects services to start; it does not stop an already-running warehouse. Use `down` first if changing an existing core instance to workspace-only operation.

## Editor entry point

Open Datacon in an editor supporting Dev Containers, then reopen using `.devcontainer/devcontainer.json`. The descriptor initialises local credentials and starts the default instance's workspace and warehouse, opening `/workspaces` as user `developer`. Leave `COMPOSE_PROJECT_NAME`, `DATACON_INSTANCE` and `DATACON_STATE_DIR` unset for this default editor route; named instances use the terminal or the editor's attach-to-running-container feature. The descriptor deliberately leaves services running when the editor closes; use `./datacon down` to stop them. The installed VS Code Dev Containers CLI successfully exercised the descriptor on 2026-10-29; graphical editor attachment/reopening remains untested.

## Candidate versions and evidence boundary

| Component | Candidate | Qualification remaining |
| --- | --- | --- |
| Workspace image | `python:3.15.2-slim-bookworm`, digest pinned in Dockerfile | ARM64 build passed; AMD64 and OS package locks remain |
| Warehouse image | `pgduckdb/pgduckdb:17-v1.1.1`, digest pinned in Compose; PostgreSQL 17.7, SQL extension 1.1.0 | ARM64 smoke passed; AMD64 and full RLS/concurrency matrix remain |
| Python dependency set | Exact versions in `requirements/workspace.txt`, including `jsonschema==4.26.0` and `rpds-py==2026.9.1` | Clean Python 3.15.2 binary install and reference passed on ARM64; wheel hashes and AMD64 remain |
| Opharma | Commit in `platform/reference.json` | Local reference and identical replay passed; native Snowflake remains separate |

These are candidate pins, not complete release locks. Both external image inputs use immutable digests; Compose's local workspace build tag is not a release identity. Docker builds run `pip check`, and the ARM64 clean build passed. OS package locks and wheel hashes remain required before releasing an approved baseline. GX, ODCS conversion tools and Snowflake clients will be qualified through their backlog items rather than installed implicitly on startup.

Python 3.15.2 was released on 2026-10-25. The official image manifest lists the selected tag for ARM64 and AMD64. `rpds-py` was updated from 0.30.0 to 2026.9.1 because that release publishes CPython 3.15 Linux wheels for both target architectures. Registry metadata does not establish installation or runtime compatibility. See [Python downloads](https://www.python.org/downloads/) and [rpds-py 2026.9.1](https://pypi.org/project/rpds-py/2026.9.1/).

Observed runtime checks and remaining limits are recorded in [the core runtime evidence](evidence/2026-10-29-core-runtime.md). The [initial candidate evidence](evidence/2026-10-29-core-candidate.md) preserves the earlier access diagnosis.

Sources: [official Python image manifest](https://github.com/docker-library/official-images/blob/master/library/python), [pg_duckdb image build matrix](https://github.com/duckdb/pg_duckdb/blob/v1.1.1/.github/workflows/docker.yaml), [pg_duckdb settings](https://github.com/duckdb/pg_duckdb/blob/v1.1.1/docs/settings.md), [Compose profile behaviour](https://docs.docker.com/compose/how-tos/profiles/) and [Dev Container reference](https://github.com/devcontainers/spec/blob/main/docs/specs/devcontainerjson-reference.md).
