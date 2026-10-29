# Datacon

A versioned development environment and working method for building governed data pipelines in independent delivery repositories.

**Current state:** planning documents and repository conventions are prepared. The Dev Container, task commands and runtime have not been implemented. Git initialisation was attempted but this session cannot write `.git`; no commit or remote has been created. See [the bootstrap commands](CONTRIBUTING.md#initial-repository-bootstrap). Repository bootstrap remains tracked in DC-001.

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

1. **DC-001: record the starting point.** Initialise Git, review and commit these documents and conventions, then establish the remote and review controls.
2. **DC-007/DC-008: establish evidence and pins.** Reproduce the pinned Opharma reference in an approved isolated environment and record actual results while qualifying the initial toolchain.
3. **DC-002/DC-003: deliver the first working increment.** Start a non-root workspace and PostgreSQL/pg_duckdb, open an independent delivery checkout, run meaningful checks and preserve uncommitted work across recreation.
4. **DC-014–DC-016: prove the target early.** Prepare Snowflake access alongside local work, then demonstrate S2/S4 and one native Semantic View. Full OpenMetadata integration follows and remains required for v1.

Every completed backlog item must point to observed evidence. Generated artefacts and static checks do not establish native deployment success.
