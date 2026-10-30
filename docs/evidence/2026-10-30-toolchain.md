# DC-007 toolchain qualification

Recorded: 2026-10-30. Implementation branch: `feat/DC-007-toolchain`, based on `dbc609095ac25b260c8b7a3cb7833bd4926b4809`. Local runs include uncommitted implementation changes; their input hashes identify the tested source. Native AMD64 execution of this increment is pending. DC-007 remains open until that evidence is inspected.

## Native ARM64 results

- Host: macOS ARM64, Python 3.14.8; Docker Engine 29.9.2, Compose 5.6.1; native ARM64 daemon.
- **48 host tests passed** on both Python 3.14.8 and 3.12.15; Compose validation, local documentation links and whitespace checks passed.
- **Two uncached toolchain builds passed**, with identical complete OS and Python inventories. Python 3.14.8 and all 68 locked distributions installed from binary wheels; `pip check` passed. The image is about 678 MiB (710,733,009 bytes for the recorded second build); this is an image size, not runtime memory use.
- Actual restricted PostgreSQL access through SQLAlchemy/psycopg2, transaction rollback, GX success and deliberate quality failure passed. Fixture tables were removed afterwards.
- With Docker networking disabled: ODCS 3.1.0/3.2.0 JSON/YAML validation, invalid-contract rejection, unknown-version rejection, corrupted-schema rejection and deterministic five-expectation GX export/load all passed.
- An incorrect wheel hash failed specifically with pip's hash-integrity error. The candidate lock preparation independently downloaded and hashed all 83 selected ARM64/AMD64 wheels.
- **Two uncached core regression builds passed**, including matching checkout/image readiness, basic RLS/DuckDB smoke, and both Opharma runs: 35 tests, one expected skip, all 14 initial/replay checkpoints and unchanged table multisets.
- **Delivery regression passed**, including retained dirty host/volume checkouts, cross-project access denial, scoped reset and credential preservation. The optional tool job read both checkout types, wrote through the host bind mount, and queried the selected project's database as its restricted role.

The [toolchain summary](2026-10-30-toolchain/arm64/qualification.json), [first inventory](2026-10-30-toolchain/arm64/build-1-inventory.json), [second inventory](2026-10-30-toolchain/arm64/build-2-inventory.json), [offline results](2026-10-30-toolchain/arm64/build-2-offline.json) and [SQL/GX results](2026-10-30-toolchain/arm64/build-2-smoke.json) retain measured evidence. See also [core regression](2026-10-30-toolchain/arm64-core/qualification.json), [readiness report](2026-10-30-toolchain/arm64-core/build-2-ready.txt) and [delivery regression](2026-10-30-toolchain/arm64-projects/qualification.json).

Only qualification containers/networks were removed. Named volumes, credentials and dirty acceptance checkouts remain. No default-instance container was rebuilt or stopped.

## Scope and dependency decision

GX 1.24.1 and Data Contract CLI 1.2.8 exclude Python 3.15. The optional Python 3.14.8 image is therefore presented for Tech Lead review; the primary workspace remains 3.15.2. [The toolchain guide](../TOOLCHAIN.md) records exact versions, source links, lock refresh and the shared native qualification command.

Snowflake Connector 5.1.0 and snowflake-sqlalchemy 2.1.0 loaded and compiled SQL locally. **No native Snowflake connection or query ran**; DC-014–DC-016 still need the target environment. Full ODCS/GX business-rule mapping, catalogue integration, WSL, resource certification, release publication and enforced review controls remain their own backlog items.
