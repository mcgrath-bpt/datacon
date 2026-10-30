# Datacon backlog

Updated: 2026-10-30. Source: confirmed user requirements, [PLAN.md](PLAN.md), and [Opharma PR #1](https://github.com/mcgrath-bpt/opharma/pull/1) at `b43c6897f6bdda2adcf60fc468fe8aaff31f52eb`.

This backlog was initially committed in `601cee3`. The canonical remote is [mcgrath-bpt/datacon](https://github.com/mcgrath-bpt/datacon); no GitHub issues have been created. IDs remain stable when items are split or promoted to an issue tracker. Owners below are responsibility types, not assignments sent to individuals.

## Operating rules

- **P0:** needed for the first usable local environment or the early Snowflake proof.
- **P1:** needed for broader project adoption, governance and the first supervised agent delivery.
- **P2:** extend only when a delivery requires it.
- **OPEN:** implementation remains. **NEEDS_ENVIRONMENT:** preparation can proceed; native acceptance requires the named environment. **DONE:** acceptance has evidence attached. **PARKED:** intentionally deferred.
- Each implementation PR cites its backlog ID, acceptance evidence and limitations. Record platform versions, project commit, contract/fixture hashes and query IDs where applicable.
- Do not mark native validation complete using generated files, static analysis or another platform's results. A missing optional environment is a visible skip, never a pass.
- Keep completed items and evidence links. Review priorities as real deliveries expose needs; do not silently remove requirements.

## Milestones and order

| Milestone | Exit condition | Scheduling intent |
| --- | --- | --- |
| M0 | Reproducible dependency choices, Opharma source pin, release conventions and Snowflake connection plan | Start immediately with implementation; discover access requirements on day one |
| M1 | New joiner can open an independent project, run local checks and use a semantic bundle within the resource envelope | First local iteration; platform certification may continue alongside M2 |
| M2 | Native S2/S4 proof and one working Snowflake Semantic View | First two short iterations, subject to target access; precedes catalogue completion |
| M3 | Catalogue, broader use cases, target semantics and evolution work reliably | After the first native proof |
| M4 | An agent proposes a pipeline that passes independent evaluation and human review | After contracts, semantics and test execution are reliable |

Critical path: **DC-007 → DC-002/DC-008 → DC-003 → DC-015**, with **DC-014** starting independently. Add **DC-013 → DC-016** for native semantic proof. OpenMetadata and a complete PostgreSQL port are not dependencies of that path.

OpenMetadata is a required Datacon v1 platform component. DC-018–DC-020 must pass before the complete v1 release; their placement after the early Snowflake proof is sequencing, not optional scope. See the [v1 service inventory](docs/V1_SERVICES.md) for the full five-container environment, short-lived jobs and lightweight core mode.

## Foundation and developer experience

### DC-001 — Establish repository and release discipline

**P0 · M0 · OPEN · Owner: Tech Lead · Dependencies: none**

Create the platform Git repository/history, agree its remote, and commit the design/backlog/handbook with ignore rules, LF handling, contribution conventions and PR guidance. Define versioned image/tool releases and a project compatibility policy. Keep source and configuration templates in Git; credentials, runtime databases and personal checkout paths stay out.

Progress, 2026-10-29: the user created initial commit `601cee3` on `main`, containing the design and repository conventions. Approved Git writes created `feat/DC-002-core-runtime` with all existing work preserved. The user subsequently supplied the public GitHub repository, now configured as `origin`; its initial MIT licence commit `6b955ac` is preserved alongside the local history. Protected reviews and release policy/locks remain outstanding, so this item stays open.

**Done when:** a fresh checkout identifies its approved platform version; release inputs are pinned; a delivery adopts releases under the Tech Lead's compatibility/upgrade policy without sharing platform source/history; initial history and remote location are recorded.

### DC-002 — Build the minimal Dev Container and core runtime

**P0 · M1 · OPEN · Owner: platform maintainer · Dependencies: DC-007**

Package a non-root Linux workspace, Git, Python and required SQL tools. Supply workspace-only and core modes; core adds PostgreSQL/pg_duckdb, while quality/generation execute as jobs. Provide terminal and editor entry points, readiness checks and useful logs.

Progress, 2026-10-29: Dockerfile, Compose services, Dev Container descriptor and `datacon` launcher implemented. Host tests, Compose validation, ARM64 build/readiness and SQL/RLS smoke pass. The installed Dev Containers CLI successfully runs the descriptor; graphical editor attachment and fresh-machine/other-host acceptance remain. See [runtime evidence](docs/evidence/2026-10-29-core-runtime.md) and [the core quick-start](docs/CORE_QUICKSTART.md).

Progress, 2026-10-30: actual VS Code graphical attachment, project terminal/database selection and saving/reopening a delivery file passed on the existing Mac. The complete ARM64 core regression passed again with 41 host tests. Fresh-machine acceptance remains open. See [delivery/editor evidence](docs/evidence/2026-10-30-delivery-workspaces.md).

**Done when:** a clean machine with documented prerequisites opens the workspace and runs a local smoke test; neither OpenMetadata, Airflow, a notebook server nor a model server starts by default.

### DC-003 — Attach independent delivery repositories safely

**P0 · M1 · OPEN · Owner: platform maintainer · Dependencies: DC-001, DC-002**

Support cloning/opening one or more independent delivery repositories from inside a Datacon workspace, with host-mounted checkouts also available. Keep compatibility metadata minimal: approved release/capabilities plus working directory and commands when needed. Namespace project services/data; optional task containers and delivery descriptors must use the approved baseline rather than define separate toolchains.

Progress, 2026-10-29: actual `down`/`up` preserved an uncommitted Opharma file, its Git revision/status, home state, a database row and credentials. A fresh instance had separate workspace/home/database state, refused name reuse and left the original intact after shutdown. Separate per-project database identities within one instance, host-mounted checkout configuration and two independent delivery repositories in one instance remain outstanding. See [runtime evidence](docs/evidence/2026-10-29-core-runtime.md).

Progress, 2026-10-30: `project` registration supports existing host and volume checkouts, separate database identities, scoped database reset and generated editor configuration. Native ARM64 acceptance used pinned Opharma plus an independent host Git fixture with spaces/dollar in its path. Reprovisioning, both cross-project access denials and resetting A while preserving B passed; recreation preserved dirty files and credentials. Native AMD64 [CI run 40972038473](https://github.com/mcgrath-bpt/datacon/actions/runs/40972038473) also passed the same project checks and both uncached core builds; evidence was downloaded and digest-verified. The existing-core workflow is complete; optional approved dependency environments and release/capability adoption await DC-001/DC-007/DC-032, so the broader item remains open. See [the guide](docs/DELIVERY_WORKSPACES.md) and [evidence](docs/evidence/2026-10-30-delivery-workspaces.md).

**Done when:** two repositories work inside one Datacon instance and retain independent histories; approved dependencies can be isolated where required; container recreation preserves retained uncommitted files; project A's reset cannot affect B; Opharma keeps its existing layout. No checkout is copied into Datacon or silently modified.

### DC-004 — Certify macOS ARM64 and WSL 3.0.3

**P0 · M1 · NEEDS_ENVIRONMENT · Owner: platform maintainer · Dependencies: DC-002, DC-003**

Exercise the workflow on an actual Windows host with WSL package 3.0.3 and WSL 2 distribution mode, as well as macOS ARM64. Document Linux-filesystem checkout placement, container runtime settings, LF/executable permissions, UID/GID behaviour, ports, paths with spaces, mounts and file watching.

**Done when:** recorded host/runtime versions and a cold-start/reopen/test transcript exist for both platforms. Linux AMD64 CI is additional evidence, not a replacement for the WSL test. Acquire the Windows test host early; do not block the first Snowflake experiment while it is being arranged.

### DC-005 — Enforce a modest resource envelope

**P0 · M1 · OPEN · Owner: platform maintainer · Dependencies: DC-002, DC-008, DC-011**

Run the core reference under a 4 GiB total container/VM allocation and two vCPUs. Bound PostgreSQL connections, DuckDB memory/threads and validation concurrency. Measure idle/peak memory, elapsed time, disk footprint and warm/cold startup. Catalogue and extra-tool profiles get independent figures.

**Done when:** the selected workload finishes without OOMs or missing work under the cap; a regression budget and measurement recipe are checked in. If the target cannot be met, record the measured minimum and an explicit design decision rather than silently raising it.

### DC-006 — Teach the working method to new joiners

**P0 · M1 · OPEN · Owner: developer-experience maintainer · Dependencies: DC-003, DC-008, DC-032, DC-033**

Turn [the working guide](docs/WORKING_GUIDE.md) into a verified onboarding path: prerequisites, clone/open, project selection, conventions, first replay, first deliberate failure, first tested change and PR. Include branch/review practice, contract evolution, debugging, secrets, reset/recovery and local-versus-target evidence.

**Done when:** a person unfamiliar with the project completes the exercise using only the guide; every command is exercised from a fresh checkout; support gaps are corrected and the observed onboarding time is recorded.

### DC-007 — Pin and diagnose the toolchain

**P0 · M0 · DONE · Owner: platform maintainer · Dependencies: none**

Qualify Python, GX Core, SQLAlchemy/drivers, ODCS tooling, PostgreSQL/pg_duckdb and base images. Define any required isolated environments or optional capabilities in the Tech Lead-owned platform repository. Add a doctor command for approved baseline identity, architecture, Docker/Compose, readiness, paths and resources. Pin schemas for offline validation.

Progress, 2026-10-29: the ARM64 workspace built with Python 3.15.2 and all pinned JSON Schema dependencies installed as binary wheels; `pip check`, smoke and the reference passed. Both input images now use verified multi-platform digests. Docker/GitHub access succeeded with approval. OS package locks, wheel hashes, AMD64 execution, GX and additional adapters remain to be qualified. See [runtime evidence](docs/evidence/2026-10-29-core-runtime.md).

Core lock increment, 2026-10-29: added SHA-256 wheel locks, dated signed Debian snapshots, complete ARM64/AMD64 OS inventories, deliberate integrity-failure checks and a shared two-build qualification script. A SHA-pinned, read-only GitHub workflow targets native AMD64. Python, existing dependency versions and input image digests are unchanged; the reference now selects the Opharma merge commit. See [core lock procedure](docs/CORE_LOCKS.md). Two uncached native ARM64 builds passed with identical inventories, both integrity-failure checks and full core/reference acceptance; see [core lock evidence](docs/evidence/2026-10-29-core-locks.md). Native AMD64 [CI run 40967301222](https://github.com/mcgrath-bpt/datacon/actions/runs/40967301222) also passed both uncached builds with identical inventories, all core/reference checks and both lock failures; the uploaded evidence was inspected and archived. GX and additional adapters remain open; DC-007 is not complete.

Handover update, 2026-10-29: user requests the latest stable Python, with 3.12 as the minimum. The workspace candidate is now `python:3.15.2-slim-bookworm`, `.python-version` records 3.15.2, and `rpds-py==2026.9.1` supplies published CPython 3.15 wheel candidates. The host launcher enforces stable Python >=3.12 and selects installed 3.14.8 on this Mac. Docker diagnostics now distinguish `access_denied`. See [HANDOVER.md](HANDOVER.md) for measured checks and remaining qualification.

Toolchain increment, 2026-10-30: the [isolated toolchain](docs/TOOLCHAIN.md) pins GX 1.24.1, Data Contract CLI 1.2.8, SQLAlchemy/PostgreSQL/Snowflake drivers and all transitive wheels under Python 3.14.8, preserving workspace Python 3.15.2. Native ARM64 repeated builds, actual PostgreSQL/GX success/failure/rollback, offline schema/export checks and deliberate integrity failures passed. Schemas are vendored at an exact upstream commit; doctor now reports readiness, input/image identity, paths and resource availability without exposing secrets. Native AMD64 [run 41023704093](https://github.com/mcgrath-bpt/datacon/actions/runs/41023704093) passed both toolchain/core builds and the full delivery workflow. All three artefacts were downloaded, digest-verified and inspected; [final evidence](docs/evidence/2026-10-30-toolchain.md) completes DC-007 technical acceptance. The isolated capability is presented for Tech Lead review in [PR #4](https://github.com/mcgrath-bpt/datacon/pull/4); no release is published. Native Snowflake execution remains DC-014–DC-016.

**Done when:** locked installs work on ARM64 and AMD64; required tools do not use floating latest versions; diagnostics explain missing prerequisites without exposing secrets. Catalogue dependencies may be locked later in DC-018.

## Reference delivery, contracts and execution

### DC-008 — Reproduce the pinned Opharma baseline

**P0 · M0/M1 · DONE · Owner: delivery maintainer · Dependencies: DC-007**

Fetch PR #1's inspected commit into an independent delivery checkout and run its existing contract, operations and test entry points. Keep SQLite as the initial reference. Capture actual results against the PR's recorded 14-checkpoint baseline; investigate differences and skips instead of copying prior success claims.

Completed, 2026-10-29: a newly built ARM64 container checked out `b43c6897f6bdda2adcf60fc468fe8aaff31f52eb` independently, validated five ODCS bundles, ran 35 tests (34 passed, one expected skip), hydrated/reconciled 14 checkpoints and repeated all 14 with `IDENTICAL_REPLAY`. Every stored table's row multiset was unchanged. [Runtime evidence](docs/evidence/2026-10-29-core-runtime.md) includes source, contract and fixture hashes plus both reports. This completes the local reference scope; DC-007's broader locks and platform qualification remain open.

**Done when:** a fresh container rebuilds the runtime database, performs identical replay and records new test/reconciliation evidence; source/fixture/contract hashes are attached. Only the agreed public fixture is exposed to builders in later benchmarks.

### DC-009 — Validate ODCS and generate supported artefacts

**P0 · M1 · OPEN · Owner: contract tooling maintainer · Dependencies: DC-007, DC-008**

Accept ODCS JSON/YAML and explicit 3.1/3.2 versions. Preserve Opharma's five bundles and multi-object identity. Evaluate existing DDL/GX exporters; document type, key, relationship and quality coverage. Record source checksums and stable object/rule IDs.

**Done when:** invalid contracts and unsupported executable rules fail clearly; repeated generation is identical; decimal/NULL/composite-key cases are covered; newer fields cannot be silently discarded. Schema evolution is handled through DC-024.

### DC-010 — Prove PostgreSQL/pg_duckdb correctness and access

**P0 · M1 · OPEN · Owner: execution maintainer · Dependencies: DC-002**

Create a small governed fixture and explicit grants/RLS. Test restricted roles against native and accelerated queries, joins, views and prepared statements; inspect plans. Add bounded concurrency/cancellation coverage and limited external-file access. Keep resource limits explicit.

Progress, 2026-10-29: non-superuser forced-RLS smoke passed on PostgreSQL 17.7 and the pinned pg_duckdb v1.1.1 image, with `DuckDBScan` observed. The image's SQL extension version is 1.1.0, verified against upstream metadata. The full access/concurrency/cancellation matrix remains open; see [runtime evidence](docs/evidence/2026-10-29-core-runtime.md).

**Done when:** permitted results agree, forbidden rows remain inaccessible, acceleration is actually exercised, and the selected build finishes the supported workload without unexplained hangs/crashes. Record unsupported query paths and use native PostgreSQL for them.

### DC-011 — Generate and run GX checks with explicit outcome policy

**P0 · M1 · OPEN · Owner: quality maintainer · Dependencies: DC-009, DC-010**

Produce GX 1.x suites from the supported ODCS subset and configure batches/Checkpoints. Retain custom domain tests. Define common PASS/ALERT/FAIL/ERROR/NO_DATA results and exit/publication policy. Exercise schema, uniqueness, ranges, relationships and exact rate boundaries with good/bad fixtures.

**Done when:** required checks execute on PostgreSQL; JSON evidence identifies source rules and observed values; intentional alerts remain distinct from structural failures; empty batches and validator errors cannot pass silently. Snowflake execution follows in M2.

### DC-012 — Standardise immutable inputs and replay evidence

**P0 · M1 · OPEN · Owner: delivery maintainer · Dependencies: DC-008, DC-009**

Expose Opharma's manifest, ready-marker, ordered-batch, hash and registry-binding conventions through reusable project interfaces. Preserve corrections, tombstones, late-arrival handling and failed/repaired retry. Maintain separate arrival/effective times.

**Done when:** mutated headers/hashes, changed replay identities and missing predecessors are detected; identical replay changes no published data; failure does not expose partial outputs or overwrite trusted state. Native transaction behaviour is proven separately in DC-015.

### DC-013 — Establish the semantic bundle

**P0 · M1 · OPEN · Owner: semantic maintainer · Dependencies: DC-008, DC-009**

Link ODCS IDs to entity grains, join/cardinality rules, authoritative sources, time semantics, aggregation/units, NULL/zero behaviour, publication cadence and access intent. Retain native SQL, DAX and TMDL with declared target mappings and verified business examples. Reuse existing Opharma definitions rather than infer new rules.

**Done when:** references validate; invalid joins, double counting and mixed snapshot/rate scopes are caught by fixtures; a machine-readable bundle can be given to an agent without requiring the catalogue or a model server.

## Early native Snowflake acceptance

### DC-014 — Bind a bounded Snowflake development environment

**P0 · M0/M2 · NEEDS_ENVIRONMENT · Owner: platform owner · Dependencies: none**

Identify an existing account, named connection/authentication method, role, warehouse, isolated schema, stage and object-store route. Prepare configuration templates and diagnostics on day one. Scope cleanup, query tags, timeouts and warehouse limits; keep credentials outside the repositories.

**Done when:** a native connectivity/permissions smoke test records query IDs, role and target bindings, and shows the runner cannot change unrelated schemas. If stage access is absent, distinguish the smoke test from full source-ingestion acceptance.

### DC-015 — Run Opharma S2 and S4 in Snowflake early

**P0 · M2 · NEEDS_ENVIRONMENT · Owner: delivery maintainer · Dependencies: DC-003, DC-008, DC-014**

Reuse the existing Snowflake runner/assets to execute S2 product activity and S4 correction/deletion handling, first at the smallest meaningful checkpoints and then across the recurring fixture. Reconcile full output multisets and diagnostics. Test identical replay, an interrupted/failed batch and repaired retry, accounting for Snowflake DDL/transaction behaviour.

**Done when:** target results and intended exceptions match the independent reference; incomplete publication stays invisible; evidence includes query IDs and hashes. GX subset checks from DC-011 are added as available. This item does not depend on catalogue deployment or a PostgreSQL rewrite.

### DC-016 — Prove one native Snowflake semantic path

**P0 · M2 · NEEDS_ENVIRONMENT · Owner: semantic maintainer · Dependencies: DC-013, DC-014**

Create a small Semantic View from versioned YAML and verify dimensions, metrics and restricted-role queries against known results. Prefer S2 data from DC-015; a direct-loaded fixture is acceptable for the initial semantic smoke test if labelled as such. Prepare verified questions and expected answers; exercise Cortex Analyst when account access permits.

**Done when:** native creation and semantic queries pass; type, grain and aggregation evidence is retained. Native query success and actual Cortex response evaluation are reported separately. No automatic DAX-to-SQL equivalence is claimed.

## Broader delivery and governance

### DC-017 — Qualify Opharma on PostgreSQL/pg_duckdb

**P1 · M3 · OPEN · Owner: execution maintainer · Dependencies: DC-008, DC-010, DC-012**

Port representative S2/S4 transformations first, then expand by need. Compare public-source outputs against SQLite and Snowflake at the same fixture/contract revision; preserve decimal/time/NULL rules and explain dialect differences.

**Done when:** the advertised supported scenarios reconcile across engines, including corrections and replay. A runnable PostgreSQL adapter must not be mistaken for a port merely because DDL was generated.

### DC-018 — Package the required v1 OpenMetadata service group

**P1 · M3 · OPEN · Owner: catalogue maintainer · Dependencies: DC-002, DC-007**

Provide the platform-owned, pinned local catalogue group: OpenMetadata server, dedicated PostgreSQL metadata database and single-node Elasticsearch. Add short-lived bootstrap/migration and ingestion jobs with the matching SDK, plus a remote endpoint connection mode. Include this group in full v1 startup and allow it to be stopped for core work. Measure resource use independently and document start/stop/backup/reset behaviour, including the absence of UI-managed ingestion scheduling in the baseline.

**Done when:** all five full-platform services pass readiness and persistence tests on the claimed hosts; failed metadata migration prevents server readiness; ingestion populates an example asset; its SDK matches the server; full-mode idle/peak requirements are recorded; and core work succeeds while the catalogue group is stopped. A warehouse reset cannot delete catalogue data or retained project checkouts. This item is required for v1 release.

### DC-019 — Publish contract, ownership and lineage information

**P1 · M3 · OPEN · Owner: catalogue maintainer · Dependencies: DC-009, DC-012, DC-013, DC-018**

Map project-qualified physical assets, multi-object contracts, ownership, glossary terms and classifications into OpenMetadata. Publish declared/run-backed lineage and immutable source links. Respect Git-managed versus UI-managed fields and inspect ODCS import losses.

**Done when:** Opharma assets can be found and traced to source contracts; repeated sync creates no duplicates; newer unmapped fields remain available in the authoritative source and are reported visibly.

### DC-020 — Publish GX results without losing meaning

**P1 · M3 · OPEN · Owner: quality maintainer · Dependencies: DC-011, DC-019**

Qualify the pinned GX/OpenMetadata integration or implement a thin external-result publisher. Preserve stable case IDs, observed values, thresholds, outcome/severity, timestamps and revision/snapshot provenance. Save results before publishing and make retries idempotent.

**Done when:** success, expected alert, hard failure and execution error can be distinguished in retained evidence; a catalogue outage can be retried without duplicate results or a false green run. The same rule is not scheduled twice by different engines.

### DC-021 — Expand cloud acceptance to S3, S1 and S5

**P1 · M3 · NEEDS_ENVIRONMENT · Owner: delivery maintainer · Dependencies: DC-012, DC-015**

Exercise workbook conversion and territory intervals, consent/identity timing, and Monday campaign publication against Snowflake. Preserve S3/S4 exceptions outside percentage-rate rows, S5 zero-contact members and campaign overlap rules.

**Done when:** all advertised checkpoints reconcile, exact threshold boundaries/NO_DATA are checked, and native access results are recorded. Logical fixture timestamps do not count as measured live delivery deadlines.

### DC-022 — Validate the existing TMDL target

**P1 · M3 · NEEDS_ENVIRONMENT · Owner: BI/semantic maintainer · Dependencies: DC-008, DC-013**

Use an appropriate Microsoft TOM/Power BI/Analysis Services environment to parse the existing model, compile DAX and refresh the declared CSV/Snowflake partitions. Retain its independent scenario facts, scorecard scope guards and daily/Monday bindings.

**Done when:** measures and rows match agreed examples, blank/rate/history behaviour is correct, and workspace/RLS/import-cache permissions are checked separately. Static text checks remain labelled static until this runs.

### DC-023 — Reuse the same checks in local and delivery CI

**P0 · M1, expanded in M2/M3 · OPEN · Owner: CI maintainer · Dependencies: DC-003, DC-008, DC-032, DC-033**

Publish stable task entry points, exit statuses and JSON evidence usable from both GitHub Actions and Opharma's Jenkins setup. Run contract, fixture and domain checks without cloud secrets. Add opt-in native jobs and compatibility tests as their adapters arrive.

**Done when:** local and clean CI invoke the same checked-in commands and approved pins; a deliberate personal-only dependency fails acceptance; required dependency reviews cannot be bypassed through ordinary merges; failures propagate; unavailable native environments are explicit skips; projects may retain their own CI provider.

### DC-024 — Manage contract, schema and semantic evolution

**P1 · M3 · OPEN · Owner: contract/semantic maintainers · Dependencies: DC-009, DC-012, DC-013**

Detect breaking changes to schema, keys, grain, metric meaning, policy and publication cadence. Generate reviewable migration/rebuild plans and compare deployed state with intended state. Bind published snapshots to contract/code versions.

**Done when:** an additive change succeeds, a breaking change is flagged, a semantic change cannot silently rebind old snapshots, and drift is visible. Destructive actions require an explicit project-scoped operation.

## Agent-assisted delivery

### DC-025 — Define the agent task and evidence interface

**P1 · M4, design in M1 · OPEN · Owner: agent tooling maintainer · Dependencies: DC-006, DC-013, DC-023**

Specify approved input contracts, semantic context, business request, allowed sources/targets, repository scope, command catalogue, limits and output/evidence schema. Include required clarifications and unsupported-operation reporting. Keep this interface independent of a particular model provider.

**Done when:** a scripted client can submit a task and inspect plan, code diff and test evidence; missing business rules are surfaced; instructions distinguish supplied data from executable workflow policy.

### DC-026 — Build independent agent evaluation

**P1 · M4 · OPEN · Owner: evaluator maintainer · Dependencies: DC-008, DC-012, DC-013, DC-025**

Package only approved public inputs for the builder; run the independent oracle/hidden expected results elsewhere. Do not mount the complete Opharma repository into that builder environment. Test novel variants involving ambiguous identity, future reference visibility, rate boundaries, replay and tombstones.

**Done when:** access tests show the builder cannot read evaluator truth; full-multiset reconciliation catches incorrect pipelines; results include repeated attempts, failure modes, runtime and target cost. Passing the visible example alone is insufficient.

### DC-027 — Demonstrate one supervised generated pipeline

**P1 · M4 · OPEN · Owner: agent tooling and delivery maintainers · Dependencies: DC-015, DC-016, DC-025, DC-026**

Have an agent propose and implement one scoped Opharma pipeline in a delivery branch using the approved patterns. Run local, quality, semantic and independent checks, then the scoped Snowflake acceptance where required. Generate a reviewable change/evidence bundle.

**Done when:** reviewers can trace requirements to mappings, code and tests; the pipeline passes the independent evaluation; failed attempts remain recorded. Merge, deployment and broad access expansion remain human decisions in this workflow.

## Extensions driven by actual deliveries

### DC-028 — Scheduling, deadlines and notifications

**P2 · Later · PARKED · Owner: operations maintainer · Dependencies: DC-015, DC-021, DC-023**

Adopt Opharma's Airflow assets or another agreed scheduler as an optional capability. Verify real source arrival, S2/S1 completion deadlines, Monday publication, missing batches, retries and notification delivery.

**Done when activated:** measured wall-clock runs and delivered alerts prove the agreed operational commitments; logical simulation is not used as SLA evidence.

### DC-029 — Enterprise governance adapters

**P2 · Later · PARKED · Owner: governance platform owners · Dependencies: DC-019, DC-020, DC-024**

Map the existing Collibra assets/lineage, Ataccama rules and Immuta policy intents to actual tenant identifiers and capabilities. Keep adapter-specific mappings separate from the core contracts.

**Done when activated:** imports and effective policy/quality behaviour are demonstrated in the target tenants with traceability and reconciliation. File export alone is not acceptance.

### DC-030 — Additional tools only when justified

**P2 · Later · PARKED · Owner: platform maintainer · Dependencies: DC-005, DC-023**

Add optional dbt, notebooks, object-store emulation, source connectors or local model tools for a named delivery. Package dependency/resource changes separately and keep core unchanged.

**Done when activated:** the named workflow is demonstrated, incremental memory/image cost is documented, and a basic user does not install or start unused capabilities.

### DC-031 — Shared catalogue and remote workspace option

**P2 · Later · PARKED · Owner: platform owner · Dependencies: DC-003, DC-018, DC-019**

Provide a shared catalogue and, if needed, remote compute for laptops below the local envelope. Reuse project manifests/releases and define tenancy, credentials, persistence and access ownership.

**Done when activated:** two users work without data/credential collisions; reconnects preserve work; upgrades and recovery are documented; the local path remains usable.

## Clarified ownership and workspace controls

### DC-032 — Enforce Tech Lead ownership of delivery dependencies

**P0 · M0/M1 · OPEN · Owner: Tech Lead · Dependencies: DC-001, DC-007**

Define the personal-experiment-to-delivery-dependency process, approved capability catalogue, platform release/support policy and review responsibilities. Any new tool/package/version that becomes a delivery prerequisite must be agreed and reproducibly provisioned through the platform repo, even for one consumer. Projects may record approved application dependencies in lockfiles; they cannot introduce a competing baseline. Use platform-owned optional features/environments to limit image growth.

**Done when:** an npm/Node-style experimental requirement is taken through request, decision, platform provision and clean delivery use; ownership and required-review controls are configured on the relevant repository paths; an unapproved dependency/baseline change is prevented from ordinary merge. CODEOWNERS alone is not counted as enforcement. Target-runtime dependencies, including Snowflake packages, are explicitly considered.

### DC-033 — Provide resume, fresh and clean acceptance workflows

**P0 · M1 · OPEN · Owner: platform maintainer · Dependencies: DC-002, DC-003, DC-007**

Allow developers to retain repositories, uncommitted changes and personal experiments. Provide a fresh approved baseline and isolated task workspace without deleting retained work. Separate persistent source/data from disposable tool state. Clean acceptance uses a committed revision and excludes personal package overlays, inherited virtual environments/node_modules and uncontrolled database contents.

**Done when:** a developer resumes a dirty workspace, starts separate clean work, and returns with all original files intact; a personal-only dependency cannot satisfy the clean run; fresh state is evidenced by baseline/image and project revision. Restarting a container with contaminated mounts does not qualify as clean.

### DC-034 — Make inter-project dependencies and promotion explicit

**P1 · M3 · OPEN · Owner: delivery maintainers and Tech Lead · Dependencies: DC-009, DC-013, DC-024, DC-032**

Describe pipeline-to-pipeline data contracts and versioned shared-code interfaces, compatibility, execution/publication order and upstream change tests. Avoid dependencies on another developer's mutable checkout path. Keep project delivery artefacts separate from the development container and record runtime-package requirements for Snowflake and other targets.

**Done when:** a small upstream/downstream example detects a breaking interface change; dependency versions and promotion order are recorded; a clean target deployment is traceable to project commits and approved platform provision. This fuller interoperability work must not delay the initial S2/S4 Snowflake proof.

## Requirement coverage

| Requirement or reference | Backlog coverage |
| --- | --- |
| Local first; Snowflake soon | DC-002, DC-008, DC-014–DC-016 |
| Everything needed to reproduce work in Git | DC-001, DC-007, DC-009, DC-023, DC-024 |
| New joiners understand the method | DC-006, DC-008, DC-013 |
| Independent delivery Git repositories, including inter-project dependencies | DC-003, DC-023, DC-034 |
| Tech Lead-owned baseline; personal installs require agreement before becoming delivery dependencies | DC-001, DC-007, DC-032 |
| Keep personal work or start fresh; enforced clean handoff | DC-003, DC-006, DC-023, DC-033 |
| Minimal/moderate laptop footprint | DC-002, DC-005, DC-018, DC-030, DC-031 |
| Future WSL 3.0.3 deployment | DC-004, DC-007 |
| GX preference without losing enterprise handoffs | DC-011, DC-020, DC-029 |
| S1 consent; S2 product; S3 territory; S4 corrections; S5 campaigns | DC-008, DC-012, DC-015, DC-017, DC-021 |
| Contracts, catalogue, lineage and discovery | DC-009, DC-018–DC-020, DC-024 |
| TMDL and Snowflake semantic definitions | DC-013, DC-016, DC-022 |
| Agent-built pipelines with credible evaluation | DC-025–DC-027; foundations in DC-012/DC-013 |

The first implementation batch is DC-001/DC-007/DC-008, followed by DC-002/DC-003, while DC-014 access preparation proceeds. Record available Snowflake and Windows test environments before scheduling their native acceptance gates.
