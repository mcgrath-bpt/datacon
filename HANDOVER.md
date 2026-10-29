# Datacon session handover

Updated: 2026-10-29. Resume this repository and its retained Docker volumes. Check Git status before changing anything; do not recreate the project or discard uncommitted files.

## Current outcome

DC-007 core lock/CI increment: local `main` was fast-forwarded to Datacon merge `dd2989c5d866e69669e0804a183832d825bc1756`; work continues on `feat/DC-007-core-locks-ci`. The previous branch is retained. Opharma now pins merge `f1d68d01e6659ba3b279b98afbb9538cbece7473`, whose tree matches the previously tested head. Existing versions and input image digests are unchanged.

Two uncached native ARM64 builds passed with identical complete dependency inventories, enforced wheel hashes and dated signed Debian snapshots. Smoke, both restart policies, deliberate lock failures and the reference all passed on both builds. There are now 31 host tests. See [core lock evidence](docs/evidence/2026-10-29-core-locks.md) and [the refresh/qualification procedure](docs/CORE_LOCKS.md). Native AMD64 CI is implemented; its actual run is still to be recorded. DC-007 remains open for GX and additional adapters.

The ARM64 core builds and runs with Python 3.15.2. Host checks, SQL/RLS smoke, the pinned Opharma reference and real retained/fresh lifecycle checks passed. DC-008’s local reference acceptance is complete. This is a development increment, not a qualified v1 release.

Read [the runtime acceptance report](docs/evidence/2026-10-29-core-runtime.md) for machine-readable evidence, exact image identities, timings and limitations. The [initial candidate report](docs/evidence/2026-10-29-core-candidate.md) retains the earlier access failures as history.

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

## Changes and observed validation

The existing launcher, core containers, database setup, reference runner and 23 host tests are now executed. Both external image inputs are pinned by multi-platform digest. The smoke assertion was corrected to SQL extension version **1.1.0**, as declared by the upstream **v1.1.1** image’s control file; the image and security assertions were retained.

- **23 host tests passed** on Python **3.14.8**, and **23 passed** on **3.12.15**.
- Compose validation, shell syntax and whitespace checks passed.
- Clean ARM64 image build installed the pinned binary dependencies under Python **3.15.2**; `pip check` passed.
- Non-root UID 1000, non-superuser database access, forced RLS through PostgreSQL and DuckDB, and an actual `DuckDBScan` passed. PostgreSQL is **17.7**.
- Opharma: **35 tests run, 34 passed, one expected static-workbook skip**; five ODCS bundles validated; **14 checkpoints** reconciled on initial hydration and identical replay. Every database table’s row multiset remained unchanged. Source, fixture and contract hashes are retained.
- Actual container recreation preserved the dirty checkout, home state, database data and credentials. A fresh instance was isolated, refused name reuse and left the retained instance intact when stopped.
- Installed VS Code Dev Containers extension **0.469.0**, CLI **0.89.0**: descriptor initialisation and `up` succeeded for `datacon-default`, `developer`, `/workspaces`. **Graphical editor attachment remains untested.**

The reference runner always creates a new checkout. The doctor reports prerequisite availability and leaves its generic `runtime_qualification` as `NOT_EXECUTED`; it does not discover previous acceptance evidence. Use the evidence reports for observed qualification.

## Next work

1. Read `AGENTS.md`, `CONTRIBUTING.md`, `docs/OPERATING_MODEL.md`, this handover and the relevant backlog item. Recheck Git/Docker access and preserve current state.
2. Finish DC-007: record native AMD64 CI for the core locks, then qualify the remaining capabilities. Qualify GX/Snowflake dependencies before making them delivery prerequisites. An isolated platform-owned environment is allowed when agreed; do not silently downgrade the workspace.
3. Finish DC-002/DC-003: graphical editor attachment, host-mounted checkout configuration, two independent deliveries in one instance and per-project database identities. Existing lifecycle checks prove instance separation, not the full per-project reset matrix.
4. Measure DC-005 under an actual 4-GiB/two-vCPU allocation, including peak memory, VM overhead and cold start. Current cached startup observations and idle samples do not qualify the envelope. Schedule actual Windows/WSL 3.0.3 acceptance separately.
5. Establish GitHub review controls and immutable release identity under DC-001/DC-032. The canonical remote is configured; no qualified release or enforced remote review policy exists yet.
6. Start early Snowflake access/semantics work (DC-014–DC-016) alongside remaining local qualification. Native Snowflake, GX, OpenMetadata and broader RLS/concurrency acceptance have not run.

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
