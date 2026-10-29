# Datacon

A versioned development environment and working method for building governed data pipelines in independent delivery repositories.

**Current state:** the existing core builds and runs with Python 3.15.2 on macOS ARM64 and native Linux AMD64 CI; both architectures passed repeated uncached builds with identical dependency inventories. [Core lock evidence](docs/evidence/2026-10-29-core-locks.md) records the actual CI run. Host tests, database smoke, the pinned Opharma reference and retained/fresh instance checks pass. [Runtime evidence](docs/evidence/2026-10-29-core-runtime.md) records the results and remaining qualification. The merged core is on `main`; the dependency-lock/CI increment is on `feat/DC-007-core-locks-ci`; `origin` is [mcgrath-bpt/datacon](https://github.com/mcgrath-bpt/datacon). This is not a released v1 platform.

Use the [core quick-start](docs/CORE_QUICKSTART.md) for commands, persistence behaviour and the current evidence boundary. Start with `./datacon check`, `./datacon config` and `./datacon doctor`.

For the next session, read [HANDOVER.md](HANDOVER.md) first. The workspace targets Python 3.15.2; host commands require stable Python 3.12 or later. Git, Docker and GitHub access succeeded with session approval; recheck access when resuming.

## Start here

1. Read [how we intend to work](docs/WORKING_GUIDE.md).
2. Read [the architecture and delivery plan](PLAN.md).
3. Use [the prioritised backlog](BACKLOG.md) to select work and record evidence.
4. Inspect [the Opharma reference](docs/OPHARMA_REFERENCE.md) for the first real delivery case.

The [operating model](docs/OPERATING_MODEL.md) defines Tech Lead ownership, personal experimentation, approved dependencies and clean versus retained workspaces.

The initial direction is local development with PostgreSQL/pg_duckdb, ODCS contracts, Great Expectations Core and versioned semantics. Snowflake validation follows early. **OpenMetadata is included in Datacon v1**, with a dedicated PostgreSQL database, Elasticsearch and ingestion tooling. The [v1 service inventory](docs/V1_SERVICES.md) defines five long-running containers for the full local platform and a two-container core mode for lighter daily work.

The target core envelope is 4 GiB and two vCPUs; it remains to be measured. Supported-host acceptance will cover macOS ARM64 and Windows/WSL package 3.0.3 with a WSL 2 Linux distribution, alongside Linux AMD64 CI.

The Tech Lead owns Datacon's shared tooling and standards baseline. Developers can experiment locally, but delivery dependencies must be agreed and reproducibly provided through the platform repository. Project repositories own their business contracts, code, semantic models, fixtures and deployment artefacts; they retain independent histories and may depend on each other through explicit interfaces. One Datacon workspace can hold several projects. Clean acceptance uses an approved release without personal additions.

Snowflake Semantic Views and the existing Opharma Power BI TMDL model are distinct native targets. Their shared business meaning will supply context and tests for supervised agent-built pipelines.

## Next implementation batch

1. **DC-001: finish repository/release setup.** The GitHub remote is configured. Establish review controls and immutable release conventions.
2. **DC-007: finish toolchain qualification.** Image digests are pinned and ARM64 reference acceptance passed. The [core lock/CI increment](docs/CORE_LOCKS.md) adds dated OS snapshots, full package inventories, wheel hashes and native AMD64 CI. Native ARM64 and AMD64 runs passed; GX and additional adapters remain open. DC-008's local reference is complete.
3. **DC-002/DC-003: extend the first increment.** Finish graphical editor/host acceptance, host-mounted checkouts and per-project identities. Retained/fresh instance checks now have runtime evidence.
4. **DC-014–DC-016: prove the target early.** Prepare Snowflake access alongside local work, then demonstrate S2/S4 and one native Semantic View. Full OpenMetadata integration follows and remains required for v1.

Every completed backlog item must point to observed evidence. Generated artefacts and static checks do not establish native deployment success.
