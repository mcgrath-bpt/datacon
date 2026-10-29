# Datacon v1 service inventory

Recorded: 2026-10-29. Status: agreed scope; workspace/warehouse build, smoke and reference acceptance passed on ARM64, while the catalogue group remains planned. See [the core quick-start](CORE_QUICKSTART.md) and [runtime evidence](evidence/2026-10-29-core-runtime.md).

OpenMetadata is a required part of the Datacon v1 platform. The Tech Lead owns its supported versions, configuration, lifecycle commands, ingestion tooling and integration tests in the platform repository. Delivery repositories supply their own contracts, ownership declarations, semantic definitions, transformation dependencies and quality rules/results. They do not provision a competing catalogue stack.

## Services that remain running

The full local reference environment has five long-running containers while in use. This count assumes one workspace and one active warehouse; additional isolated project instances increase it.

| Service name | Component | Responsibility | Persistent state |
| --- | --- | --- | --- |
| `workspace` | Datacon Dev Container | Shell, Git, Python, approved project tools, SQL clients and task commands; developers clone/open independent project repositories here | Project checkouts, including uncommitted work, in a persistent workspace |
| `warehouse` | PostgreSQL with the pg_duckdb extension | Local project tables, schemas, roles and RLS; analytical execution through the extension where qualified | Project database volume, separate from catalogue storage |
| `openmetadata` | OpenMetadata server | Catalogue web UI and API; discovery, glossary, ownership, contracts, lineage and published quality history | Authoritative catalogue records live in `metadata-db` |
| `metadata-db` | Dedicated PostgreSQL instance | OpenMetadata's application database, with its own credentials and lifecycle | Separate metadata database volume |
| `metadata-search` | Single-node Elasticsearch | OpenMetadata search and discovery indexes | Separate search volume; document rebuilding indexes from catalogue records |

DuckDB runs within the PostgreSQL extension; it is not a separate database service. The metadata database is separate from the development warehouse so that a project reset cannot erase the catalogue. One local catalogue can describe several projects using qualified asset names.

OpenMetadata supports database and search dependencies and API-driven ingestion. PostgreSQL is represented in its upstream Compose configuration. Pin and test a compatible released combination of server, PostgreSQL, Elasticsearch and ingestion SDK; do not copy development/SNAPSHOT versions into the baseline. See [deployment guidance](https://docs.open-metadata.org/v2.0.x/deployment/docker) and [the upstream PostgreSQL configuration](https://github.com/open-metadata/OpenMetadata/blob/main/docker/docker-compose-quickstart/docker-compose-postgres.yml).

## Jobs and tools that run when needed

| Task | How it runs in v1 | Trigger |
| --- | --- | --- |
| OpenMetadata bootstrap/migration | Short-lived `metadata-bootstrap` container using the matching server release | Initial setup and an explicit platform upgrade, before the server becomes ready |
| Metadata ingestion/publication | Short-lived `metadata-ingest` container with a matching SDK and selected connectors; platform adapters publish contracts, ownership, lineage and saved GX results | A documented sync command or a successful pipeline/validation workflow; retries are explicit and idempotent |
| Great Expectations Core | Approved Python environment in `workspace`; the same task interface in CI | Local validation, pipeline checks and CI; no separate quality server |
| ODCS validation and generation | Approved CLI/Python tools in `workspace` | Contract checks, DDL/migration proposals and GX suite generation |
| Semantic validation | Tools and tests in `workspace`; native Snowflake checks use a configured remote development account | Validate definitions, joins, grain and measures; deploy/query Semantic Views for native acceptance |
| Pipeline execution and tests | Project commands invoked using approved platform tools | Developer or CI invocation, including fixtures, transformations, replay and domain checks |

An ingestion run is required to populate or refresh the catalogue; starting the server alone does not discover project assets. Save quality/run evidence before attempting publication, retaining it for retry when the catalogue is stopped or unavailable.

The v1 baseline uses command-driven ingestion and API publication. Creating and scheduling ingestion pipelines from the OpenMetadata UI requires its Airflow integration and is outside this initial runtime. This is a documented capability boundary, not a requirement for an otherwise unused scheduler. See [OpenMetadata ingestion deployment options](https://docs.open-metadata.org/v2.0.x/deployment/docker).

## Startup modes and resource policy

- **Full local platform:** all five services, with bootstrap and ingestion jobs as required. This is the complete v1 onboarding and integration acceptance environment.
- **Core development:** `workspace` and `warehouse`; other services remain stopped. This is the lightweight daily mode for editing, execution, quality and semantic checks. Catalogue publication remains pending until a configured catalogue is available.
- **Remote catalogue connection:** the local core connects to an existing compatible OpenMetadata endpoint when available. Hosting a shared team catalogue is separate backlog work; v1 must still deliver and test the local catalogue group.

Choosing the core mode changes what is running, not what the platform includes. The 4 GiB/two-vCPU target applies to core development only and remains unmeasured. Measure and publish the full platform's idle, ingestion and validation peaks separately before claiming a supported minimum. The full platform is not currently promised to fit within 4 GiB.

Snowflake is a remote target, not a local container. ODCS and semantic YAML are versioned specifications processed by tools, not servers. A permanent Airflow scheduler, local LLM server, Kafka or object-store emulator is not required for this initial inventory; later delivery needs can introduce approved capabilities.

## Release acceptance and ownership

OpenMetadata packaging, populated project metadata and GX result publication are v1 release requirements tracked by DC-018, DC-019 and DC-020. They can follow the early Snowflake proof without being deferred beyond v1. The first local/core milestone is an implementation increment, not the complete v1 release.

Acceptance must demonstrate startup/readiness, migration failure handling, persistence across recreation, a project reset that preserves catalogue records, repeatable ingestion, retained evidence and successful publication retry, matching SDK/server versions, and full/core start-stop behaviour. Record actual host/architecture and resource measurements. Platform-managed volumes and lifecycle commands must preserve both catalogue data and retained project checkouts unless an explicit scoped reset is requested.

Core startup, smoke, reference replay and instance persistence have been demonstrated on macOS ARM64. The complete service inventory, resource envelope and native integrations remain unqualified.
