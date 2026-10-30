# Optional toolchain and diagnostics

Recorded: 2026-10-30. DC-007 provides a platform-owned, finite tool job alongside the Python 3.15.2 workspace. Delivery business logic remains in independent repositories. These pins and the isolated interpreter are a baseline dependency decision for Tech Lead review through the DC-007 PR; no immutable Datacon release is claimed.

## Compatibility decision

GX 1.24.1 and Data Contract CLI 1.2.8 declare Python `>=3.10,<3.15`. Use an isolated **Python 3.14.8** image for these capabilities. The workspace remains **3.15.2**, and host tooling still requires stable **3.12 or later**. Do not bypass upstream Python constraints or install this environment into a developer's home directory. See [GX release notes](https://docs.greatexpectations.io/docs/core/changelog/) and the exact [GX](https://pypi.org/pypi/great-expectations/1.24.1/json) and [Data Contract CLI](https://pypi.org/pypi/datacontract-cli/1.2.8/json) release metadata.

| Tool | Exact version | Qualified operation |
| --- | --- | --- |
| Python, workspace | 3.15.2 | Existing core and Opharma reference |
| Python, optional job | 3.14.8 | Toolchain imports, validation and SQL checks |
| GX Core | 1.24.1 | Valid and deliberately invalid PostgreSQL fixtures |
| SQLAlchemy | 2.1.6 | PostgreSQL execution/rollback and Snowflake SQL compilation |
| psycopg2-binary | 2.9.13 | Actual restricted PostgreSQL connection |
| Snowflake Connector | 5.1.0 | Import; target execution remains DC-014–DC-016 |
| snowflake-sqlalchemy | 2.1.0 | Dialect loading and SQL compilation |
| Data Contract CLI | 1.2.8 | Deterministic GX export loaded by GX |
| PyYAML | 6.0.3 | Offline YAML contract parsing |
| ODCS JSON schemas | 3.1.0 and 3.2.0 | Valid/invalid JSON and YAML, pinned offline |

[Direct requirements](../requirements/toolchain.in), the [complete hash lock](../requirements/toolchain.txt) and [wheel provenance](../requirements/toolchain-wheels.json) record 68 distributions and 83 independently downloaded and SHA-256-verified wheels for CPython 3.14 on Linux ARM64/AMD64. All transitive dependencies are exact. The image uses `--only-binary=:all: --require-hashes`, followed by `pip check`. Bootstrap pip and every OS package come from the [digest-pinned Python image](../containers/toolchain/Dockerfile); no OS packages are installed or updated in that image. Qualification records its complete OS/Python inventories and compares two uncached builds.

The workspace's existing OS snapshot, wheel locks and PostgreSQL/pg_duckdb image pins are retained. Catalogue dependencies remain DC-018. This increment does not implement the complete ODCS-to-GX mapping in DC-009/DC-011 or claim native Snowflake, WSL or 4-GiB resource acceptance.

## Run a finite tool job

```sh
./datacon up
./datacon tools
./datacon tools -- python /opt/datacon/scripts/contracts.py /workspaces/my-project/example.odcs.yaml
./datacon tools -- datacontract export great-expectations /workspaces/my-project/example.odcs.yaml --schema-name orders
```

`tools` builds the pinned optional image and runs a non-root job with `--rm --no-deps`. With no command it runs capability smoke, including bounded PostgreSQL checks. It does not start the warehouse implicitly; `up` provides it. Ordinary `up` does not build or run the optional toolchain. The job has a 1536-MiB/one-CPU limit, uses `restart: "no"`, and terminates on completion. The core's long-running services keep `restart: unless-stopped`. These limits are configuration, not resource certification.

The job shares the instance's persistent `/workspaces` volume and registered host checkout mounts, with the recorded workspace UID/GID. Run `up` after upgrading to regenerate an older instance's mount overlay. Its home is disposable and its Python environment is image-owned. A supplied command can intentionally change mounted delivery files; clean delivery acceptance remains DC-033. Named project credentials remain available through existing project secret files; default smoke uses only the restricted instance `developer` identity. It creates unique SQL tables and drops them in `finally`.

## Offline schema validation

The [schema manifest](../platform/schemas.json) records upstream commit, source URL, Git blob identity and SHA-256 for each vendored schema. The files retain the [Apache-2.0 licence](../platform/schemas/LICENSE). Upstream version-named files can change, so version names alone are insufficient pins; see [upstream schema versioning](https://github.com/bitol-io/open-data-contract-standard/blob/d3e1cb3e69849e05c9a7522abed9b27fb9af50d7/schema/README.md).

`contracts.py` checks hashes before selecting the declared `apiVersion`, rejects unsupported versions, and uses a JSON Schema registry without a network retriever. Only local schema references are present. JSON and YAML are supported; input errors report paths/rules without copying data values. A valid schema does not prove business correctness. Opharma's independently vendored schema and reference behaviour remain unchanged.

## Read-only diagnosis

```sh
./datacon doctor --json
./datacon doctor --json --require-ready
```

The normal command succeeds when Docker and Compose are accessible, including before initialisation. It reports missing/denied prerequisites, host and daemon architecture, resource availability, repository/state paths, credential-file completeness without reading their values, and selected service states, image identities and configured resource limits. It never initialises credentials or starts services. Docker environment, secret contents and raw connection errors are excluded.

`--require-ready` also requires healthy workspace/warehouse services, matching workspace runtime-input fingerprint and warehouse image digest, and native host/daemon architecture. A retained older image without a fingerprint is visibly unmatched. Run `up` to rebuild it while preserving volumes. The fingerprint covers runtime definitions, scripts, locks and schemas; documentation changes do not alter it. It identifies checkout inputs, not a released/approved baseline. `release` remains null and `runtime_qualification` remains `NOT_EXECUTED`: the doctor does not turn readiness into acceptance evidence.

## Refresh and qualification

Agree direct requirements/interpreter changes with the Tech Lead first. For a new candidate, resolve [toolchain.in](../requirements/toolchain.in) with the exact image's pip using `install --dry-run --only-binary=:all: --report` on each architecture. Emulation may prepare candidates but cannot satisfy native acceptance. Then:

```sh
python3.14 scripts/lock_toolchain.py arm64-report.json amd64-report.json --output candidate-locks
```

This rejects architecture version differences and source distributions, downloads every selected wheel and independently checks its published hash. Review candidate files before replacing the two committed lock/provenance files. Preserve credentials and old volumes. Run:

```sh
python3.14 scripts/qualify_toolchain.py --expected-architecture arm64
python3.14 scripts/qualify.py --expected-architecture arm64
python3.14 scripts/qualify_projects.py --expected-architecture arm64
```

Use the installed supported host interpreter and `amd64` on a native AMD64 machine. CI invokes the same scripts in separate core and toolchain jobs. Toolchain qualification uses a unique instance, two uncached builds, complete inventory comparison, a real incorrect-wheel-hash rejection, network-disabled ODCS/GX-export checks, a corrupted-schema rejection and actual PostgreSQL/GX pass/fail/rollback checks. Only its containers are removed afterwards; named volumes and matching credentials remain. Native Snowflake tests are explicitly not executed without a target account.
