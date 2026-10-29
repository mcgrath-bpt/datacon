# Core runtime acceptance

Recorded: 2026-10-29. Work: DC-002/DC-003/DC-007/DC-008/DC-010, on `feat/DC-002-core-runtime`, based on design commit `601cee36cf6e9c6970620bca34ea0046eb6ea90c`. This qualifies the observed ARM64 core increment, not a complete v1 release.

## Environment and access

Git branch creation, GitHub HTTPS access and Docker access succeeded with session approval. The earlier sandbox failures remain historical evidence in [the initial candidate report](2026-10-29-core-candidate.md). No ownership, global permissions or remote configuration was changed.

The host is macOS ARM64. Docker Desktop 4.97.0 runs Engine 29.9.2, with Compose 5.6.1. The daemon exposes four CPUs and 14,636,896,256 bytes of memory (about 13.6 GiB). Host checks used Python 3.14.8 and 3.12.15. The container ran Python 3.15.2 with binary wheels for all six pinned dependencies; `pip check` passed. Python's [release list](https://www.python.org/downloads/) still identifies 3.15.2 as the latest stable release at this check.

[Runtime observations](2026-10-29-core-runtime/runtime.json) record actual image IDs, installed package versions, health, limits and a resource sample. Both input images now use the verified multi-platform index digests:

- Python: `sha256:4e03260adeeebafccd084f3584e6b84823aba5651cfb53ef8a078ed441ddf9cd`.
- pg_duckdb: `sha256:302d06d005b6b26512ed68f3d752842641c3c36504d18e8a76e60e3354e00d22`.

Manifest inspection lists ARM64 and AMD64. Only ARM64 was built and executed. Installed PostgreSQL is 17.7 (`Debian 17.7-3.pgdg12+1`). OS packages and wheel hashes remain release-lock work; image digest pins alone do not make the workspace build fully reproducible.

## Observed checks

| Check | Result |
| --- | --- |
| Host tests | 23 passed on Python 3.14.8; 23 passed on Python 3.12.15 |
| Compose, shell syntax and whitespace | Passed |
| Core build/start | Clean initial image build and dependency install passed; both services became healthy |
| Non-root smoke | UID 1000, writable workspace, Git and `pip check` passed |
| Database smoke | Developer is neither superuser nor RLS-bypass; both engines returned only the permitted value 7; `DuckDBScan` observed; test objects rolled back |
| Opharma | 35 tests run: 34 passed, one expected skip because the static workbook is absent |
| Contracts | Five ODCS 3.1.0 bundles validated; combined contract hash `27073c77045040ad84e10495e2a2a19995bfd7b94d1c9fdb0ca8b05ca8bf2cbe` |
| Initial hydration and identical replay | All 14 checkpoints reconciled on each run; replay reported `IDENTICAL_REPLAY`; every stored table's row multiset remained unchanged |
| Container recreation | Uncommitted project file, Git revision/status, home probe, database row and local credentials preserved after `down`/`up`; workspace container ID changed |
| Fresh instance | Separate empty workspace/home/database; smoke passed; name reuse rejected; original data survived creation and shutdown of the fresh instance |
| Dev Containers entry point | Installed extension 0.469.0 / CLI 0.89.0 ran the descriptor's initialisation and `up` successfully; selected `datacon-default`, user `developer`, folder `/workspaces` |

The first smoke run failed because it expected SQL extension version `1.1.1`. The installed image reports `1.1.0`, matching the [v1.1.1 control file](https://github.com/duckdb/pg_duckdb/blob/v1.1.1/pg_duckdb.control). The assertion now checks that declared version. The image version, RLS assertions and accelerated-plan assertion were retained. Smoke subsequently passed in both the retained and fresh instances.

Evidence: [host checks](2026-10-29-core-runtime/host-checks.txt), [smoke transcript](2026-10-29-core-runtime/smoke.txt), [source hashes](2026-10-29-core-runtime/opharma-source.json), [reference summary and 95 contract/fixture hashes](2026-10-29-core-runtime/opharma-summary.json), [first hydration](2026-10-29-core-runtime/opharma-first-run.json), [replay](2026-10-29-core-runtime/opharma-replay.json), [lifecycle observations](2026-10-29-core-runtime/lifecycle.json).

## Retained state and reproduction

The independent reference checkout is `/workspaces/opharma-2026-10-29T17-33-23Z-4729fa81`, at `b43c6897f6bdda2adcf60fc468fe8aaff31f52eb`. Its runtime database and full generated fixture remain under `/workspaces/.datacon-evidence/opharma-2026-10-29T17-33-23Z-4729fa81/`. Neither database nor fixture content is committed to Datacon.

The retention probe `.datacon-retention-20261029.txt` remains uncommitted in the project and in the developer home. Its SHA-256 is `b897e681727fed10ba1c92023da5c80854f7153129aec60e2b254b352c4c9c75`. `workspace.datacon_retention_20261029` contains the corresponding database probe. These were created solely for acceptance. No existing project file was changed.

The default instance remains running. `acceptance-20261029-core` is stopped with its volumes and local credentials retained. The local harness and detailed lifecycle log are in ignored `.local/acceptance/`; its fixed probe names deliberately prevent accidental repeated seeding. For a new run, use unused probe/instance names, write and hash an uncommitted project file plus home/database probes, then follow the lifecycle commands recorded in the JSON. Verify contents, Git revision/status and unchanged credentials after each transition. Do not delete volumes to rerun acceptance.

The standard repeatable reference route remains:

```sh
./datacon check
./datacon config
./datacon doctor --json
./datacon up
./datacon smoke
./datacon reference
```

Each `reference` invocation uses a new checkout and fixture. To exercise the descriptor with an installed Dev Containers CLI, run `devcontainer up --workspace-folder .`; this session used the CLI bundled with the installed VS Code extension. An actual graphical editor attachment/reopen has not been observed.

## Measurement limits and remaining acceptance

Cached-image `down`/`up` readiness took 11.843 seconds; starting the fresh instance with cached layers took 11.425 seconds. These are single observations, not cold-build benchmarks. At 2026-10-29 17:43:20 UTC, an idle sample showed 2.68 MiB workspace and 25.66 MiB warehouse memory; peak memory and VM overhead were not measured. Both containers reported no OOM kill. The larger VM allocation means the 4-GiB/two-vCPU envelope remains unqualified.

AMD64, actual Windows/WSL 3.0.3, graphical editor attachment, two independent delivery repositories in one instance, host-mounted checkouts, project database identities, full RLS/concurrency/cancellation coverage, immutable OS/wheel locks, clean release CI, native Snowflake, GX and OpenMetadata remain outstanding. DC-008's pinned local reference acceptance is complete; the broader foundation and release items remain open.
