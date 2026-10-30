# Datacon session handover

Updated: 2026-10-30. Preserve retained Docker volumes, credentials and dirty delivery checkouts. Recheck Git/Docker access each session.

## Current outcome

PR #3 is merged. Work started from clean `main` at `dbc609095ac25b260c8b7a3cb7833bd4926b4809` on `feat/DC-007-toolchain`.

DC-007 now has a platform-owned optional tool image: Python 3.14.8, GX 1.24.1, Data Contract CLI 1.2.8, SQLAlchemy 2.1.6, psycopg2-binary 2.9.13, Snowflake Connector 5.1.0 and snowflake-sqlalchemy 2.1.0. GX and the contract CLI exclude Python 3.15; the main workspace remains Python 3.15.2. All 68 distributions are locked with 83 verified wheel hashes, and the optional base image is digest-pinned. Dependency/interpreter adoption is presented for Tech Lead review in the DC-007 PR.

`./datacon tools` runs a finite non-root job. It shares registered checkout mounts and project secrets while keeping its interpreter/home separate. ODCS 3.1/3.2 schemas are pinned to an upstream commit and SHA-256, with offline JSON/YAML validation. `doctor --require-ready` checks healthy core services, workspace input fingerprint, warehouse digest and matching native architecture; ordinary doctor remains usable before initialisation. No approved immutable release is claimed.

Native ARM64 toolchain qualification passed two uncached builds with identical OS/Python inventories, PostgreSQL/GX pass/fail/rollback, network-disabled schema/export checks and deliberate wheel/schema integrity failures. The two-build core regression and project workflow passed, including actual toolchain access to host/volume checkouts and a restricted project database. All 48 host tests passed under Python 3.14.8 and 3.12.15. Native AMD64 CI for this increment is pending; DC-007 remains open until its results are inspected. See [the toolchain guide](docs/TOOLCHAIN.md) and [evidence](docs/evidence/2026-10-30-toolchain.md).

The default workspace and warehouse remain running/healthy. New qualification instances have had only their containers/networks removed; volumes, credentials and dirty fixture checkouts remain. Raw evidence is under `.local/toolchain-qualification/2026-10-30-arm64/`, `.local/qualification/2026-10-30-dc007/` and `.local/project-qualification/2026-10-30-dc007-tools/`. An earlier project regression is also retained under `.local/project-qualification/2026-10-30-dc007/`. Use each `qualification.json` for its unique instance name. None of these is a release or native Snowflake acceptance.

## Decisions to preserve

- Datacon is the Tech Lead-owned platform/tooling/standards repository. Pipeline projects, starting with Opharma, retain independent Git histories/releases in a persistent development workspace.
- Developers may experiment locally. Delivery dependencies require Tech Lead agreement and reproducible provision through Datacon. Fresh instances must not erase retained work.
- Long-running Docker services use `restart: unless-stopped` (equivalent to `--restart=unless-stopped`). Preserve this for future platform services. Explicitly stopped containers stay stopped; `down` removes them until a later `up`. One-off jobs remain finite.
- OpenMetadata is required in v1. The full inventory is workspace, PostgreSQL/pg_duckdb warehouse, OpenMetadata server, separate metadata PostgreSQL and Elasticsearch. Ingestion/validation are jobs. This increment implements only workspace and warehouse.
- Prefer GX Core, ODCS contracts and versioned semantics. Early Snowflake S2/S4 and a Semantic View precede completion of catalogue integration. Do not silently introduce project-owned toolchains.
- Aim for a measured 4-GiB/two-vCPU core. This target remains unqualified. Test macOS ARM64, Linux AMD64 and an actual Windows host with WSL package 3.0.3 and a WSL 2 distribution.
- Prefer the latest stable Python, pinned exactly; workspace target **3.15.2**, host minimum stable **3.12**. Container compatibility is now observed for the initial dependency set; GX/Snowflake dependencies remain to be qualified.
- Use British English, prefer “indifferent”, and use `YYYY-MM-dd` dates with an explicit timezone where needed. “Test yourself, before you wreck yourself.”

## Git and session access

Workspace: `/Users/mmcgrath/Documents/dev/00-base/datacon`.

Previous branch (retained): `feat/DC-002-core-runtime`, created from design commit `601cee36cf6e9c6970620bca34ea0046eb6ea90c`. The user supplied the canonical public remote [mcgrath-bpt/datacon](https://github.com/mcgrath-bpt/datacon), configured as `origin` at `https://github.com/mcgrath-bpt/datacon.git`. Its initial MIT licence commit `6b955ac` was joined with the local design history on `main` and included in the feature branch. Preserve both histories; use ordinary pushes. Check `git log --graph --oneline --all`, `git branch -vv` and `git status --short --branch` for current commits and upstream state. Core implementation goes through PR review into `main`.

The default sandbox still denies Git metadata writes, Docker socket access and shell DNS/network access. Unlike the previous session, approval is available: approved Git branch creation, Docker commands and `git ls-remote` succeeded. Docker Desktop is healthy and reachable through approved commands. Do not change ownership, reinitialise Git or assume the old restrictions are permanent; recheck access on resumption.

## Runtime state to preserve

- `datacon-default`: workspace and warehouse running and healthy at last check. Docker Engine 29.9.2, Desktop 4.97.0, Compose 5.6.1; ARM64 daemon with four CPUs and about 13.6 GiB memory.
- Workspace image observed during acceptance: `sha256:9dbfb558c35f2859e8c1a759e10ef08c353df41a08dc976838f9fd742e306a0e`. Later documentation-only rebuilds can change the image ID; consult the recorded runtime evidence and current image inspection.
- `qual-20261029223211-e63f2e99`: qualification containers removed after success; volumes and matching credentials retained. Sanitised raw output is in `.local/qualification/core-locks-arm64/`. The default containers and dirty Opharma probe were rechecked unchanged afterwards.
- `acceptance-20261029-core`: stopped after successful fresh-instance checks; its volumes and `.local/instances/acceptance-20261029-core/` credentials are retained. Do not reuse this name with `fresh`.
- Opharma checkout: `/workspaces/opharma-2026-10-29T17-33-23Z-4729fa81`, detached at `b43c6897f6bdda2adcf60fc468fe8aaff31f52eb`. Create a delivery feature branch before changing its business code.
- Reference evidence/database: `/workspaces/.datacon-evidence/opharma-2026-10-29T17-33-23Z-4729fa81/`. Only reports and hashes were copied into Datacon; runtime databases remain in the volume.
- A deliberate uncommitted `.datacon-retention-20261029.txt` probe remains in that checkout and the developer home. The database probe is `workspace.datacon_retention_20261029`. Both are acceptance artefacts; their survival is recorded. No original project file was modified.
- Local lifecycle harness/log: ignored `.local/acceptance/`. Credentials: ignored `.local/instances/`. Preserve them with their volumes; never commit them or rotate passwords for existing databases.

The 2026-10-30 qualification instances `projects-20261029230440-d2e0ed`, `qual-20261029230640-b21be4b9` and graphical instance `projects-20261029230140-2e22c5` have had only their containers/network removed; all volumes, credentials and dirty source checkouts remain. Raw evidence lives in ignored `.local/project-qualification/` and `.local/qualification/2026-10-30-core-projects/`. The graphical instance retains `editor-acceptance.txt` as an uncommitted probe. The default instance was rechecked running/healthy with its original dirty Opharma probe intact.

## Changes and observed validation

The existing launcher, core containers, database setup, reference runner and 23 host tests are now executed. Both external image inputs are pinned by multi-platform digest. The smoke assertion was corrected to SQL extension version **1.1.0**, as declared by the upstream **v1.1.1** image’s control file; the image and security assertions were retained.

- **23 host tests passed** on Python **3.14.8**, and **23 passed** on **3.12.15**.
- Compose validation, shell syntax and whitespace checks passed.
- Clean ARM64 image build installed the pinned binary dependencies under Python **3.15.2**; `pip check` passed.
- Non-root UID 1000, non-superuser database access, forced RLS through PostgreSQL and DuckDB, and an actual `DuckDBScan` passed. PostgreSQL is **17.7**.
- Opharma: **35 tests run, 34 passed, one expected static-workbook skip**; five ODCS bundles validated; **14 checkpoints** reconciled on initial hydration and identical replay. Every database table’s row multiset remained unchanged. Source, fixture and contract hashes are retained.
- Actual container recreation preserved the dirty checkout, home state, database data and credentials. A fresh instance was isolated, refused name reuse and left the retained instance intact when stopped.
- Installed VS Code Dev Containers extension **0.469.0**, CLI **0.89.0**: descriptor initialisation and `up` succeeded for `datacon-default`, `developer`, `/workspaces`. Actual graphical project attachment subsequently passed on 2026-10-30; see the current delivery evidence.

The reference runner always creates a new checkout. The doctor reports prerequisite availability and leaves its generic `runtime_qualification` as `NOT_EXECUTED`; it does not discover previous acceptance evidence. Use the evidence reports for observed qualification.

## Next work

1. Read repository instructions, this handover and the relevant backlog item; recheck Git/Docker access and preserve retained state.
2. DC-003 PR #3 is merged; preserve its qualified delivery workflow. Existing-core mounts, two repositories, project identities, scoped reset and Mac graphical attachment are implemented. Broader DC-002/DC-003 criteria still include fresh-machine acceptance and approved dependency/release adoption.
3. Finish native AMD64 toolchain CI and inspect its artefacts, then update DC-007 evidence/status. The isolated capability and dependency decision need normal Tech Lead PR review; workspace Python is unchanged.
4. Measure DC-005 under an actual 4-GiB/two-vCPU allocation, including peak memory, VM overhead and cold start. Arrange actual Windows/WSL 3.0.3 acceptance under DC-004.
5. Establish required review controls and immutable release identity under DC-001/DC-032. No qualified release or enforced remote review policy exists yet.
6. Start early Snowflake access/semantics work (DC-014–DC-016). Native Snowflake, OpenMetadata and broader RLS/concurrency acceptance have not run; basic GX/PostgreSQL capability checks have passed.

For routine core checks:

```sh
./datacon check
./datacon config
./datacon doctor --json
./datacon up
./datacon smoke
./datacon reference
```

Use `down` without volume deletion for routine shutdown. `fresh <unused-name>` retains other instances and creates new persistent state. Do not use resets or volume pruning to obtain a clean acceptance run.
