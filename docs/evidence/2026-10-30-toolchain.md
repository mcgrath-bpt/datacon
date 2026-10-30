# DC-007 toolchain qualification

Recorded: 2026-10-30. Implementation: `b5b1bef7d1c1b816f9cc44f44a0f1b355755f958` on `feat/DC-007-toolchain`. Final ARM64 core/toolchain runs used that clean committed source. The ARM64 delivery run used the recorded pre-commit implementation hashes. Native AMD64 tested GitHub's merge ref `8d84387ba36aee5154a8caa95a506163c6ad4d6f`; its runtime-input fingerprint exactly matches the ARM64 implementation. DC-007 technical acceptance is complete. [PR #4](https://github.com/mcgrath-bpt/datacon/pull/4) remains the review/adoption route; this is not a published release.

## Native ARM64 results

- Host: macOS ARM64, Python 3.14.8; Docker Engine 29.9.2, Compose 5.6.1; native ARM64 daemon.
- **48 host tests passed** on both Python 3.14.8 and 3.12.15; Compose validation, local documentation links and whitespace checks passed.
- **Two uncached toolchain builds passed**, with identical complete OS and Python inventories. Python 3.14.8 and all 68 locked distributions installed from binary wheels; `pip check` passed. The image is about 678 MiB (710,754,152 bytes for the recorded second build); this is an image size, not runtime memory use.
- Actual restricted PostgreSQL access through SQLAlchemy/psycopg2, transaction rollback, GX success and deliberate quality failure passed. Fixture tables were removed afterwards.
- With Docker networking disabled: ODCS 3.1.0/3.2.0 JSON/YAML validation, invalid-contract rejection, unknown-version rejection, corrupted-schema rejection and deterministic five-expectation GX export/load all passed.
- An incorrect wheel hash failed specifically with pip's hash-integrity error. The candidate lock preparation independently downloaded and hashed all 83 selected ARM64/AMD64 wheels.
- **Two uncached core regression builds passed**, including matching checkout/image readiness, basic RLS/DuckDB smoke, and both Opharma runs: 35 tests, one expected skip, all 14 initial/replay checkpoints and unchanged table multisets.
- **Delivery regression passed**, including retained dirty host/volume checkouts, cross-project access denial, scoped reset and credential preservation. The optional tool job read both checkout types, wrote through the host bind mount, and queried the selected project's database as its restricted role.

The [toolchain summary](2026-10-30-toolchain/arm64/qualification.json), [first inventory](2026-10-30-toolchain/arm64/build-1-inventory.json), [second inventory](2026-10-30-toolchain/arm64/build-2-inventory.json), [offline results](2026-10-30-toolchain/arm64/build-2-offline.json) and [SQL/GX results](2026-10-30-toolchain/arm64/build-2-smoke.json) retain measured evidence. See also [core regression](2026-10-30-toolchain/arm64-core/qualification.json), [readiness report](2026-10-30-toolchain/arm64-core/build-2-ready.txt) and [delivery regression](2026-10-30-toolchain/arm64-projects/qualification.json).

Only qualification containers/networks were removed. Named volumes, credentials and dirty acceptance checkouts remain. No default-instance container was rebuilt or stopped.

## Native AMD64 results

[GitHub Actions run 41023704093](https://github.com/mcgrath-bpt/datacon/actions/runs/41023704093) passed the two-build toolchain job and the complete core/delivery job on native `ubuntu-24.04` AMD64. Python/OS inventories were identical between each pair of uncached builds. Toolchain package names/versions also match ARM64. Offline ODCS/GX export, deliberate integrity failures, restricted PostgreSQL/GX success/failure/rollback, core readiness/RLS/Opharma replay and project isolation/mount/database checks passed. Linux UID 1001 was observed in both images and the tool job.

All three ZIP artefacts were downloaded and SHA-256-verified against GitHub metadata before inspection. [Artefact provenance](2026-10-30-toolchain/ci-artifacts.json) records their IDs, digests, sizes, head commit and tested merge commit. Sanitised selected reports are retained: [toolchain](2026-10-30-toolchain/amd64/qualification.json), [offline checks](2026-10-30-toolchain/amd64/build-2-offline.json), [SQL/GX checks](2026-10-30-toolchain/amd64/build-2-smoke.json), [core](2026-10-30-toolchain/amd64-core/qualification.json) and [delivery](2026-10-30-toolchain/amd64-projects/qualification.json). Text transcripts have trailing whitespace removed; the raw ZIPs remain ignored locally. The AMD64 tool image measured 673,595,928 bytes.

The final core/toolchain runtime-input SHA-256 is `4df59c2375359f8189cdda533725cbb0115b68e00b15e56393ab8656442920cb` on both architectures. The later evidence-only commit does not change these inputs. The default instance's original dirty file/home probes and database probe were rechecked intact after all local acceptance.

## Scope and dependency decision

GX 1.24.1 and Data Contract CLI 1.2.8 exclude Python 3.15. The optional Python 3.14.8 image is therefore presented for Tech Lead review; the primary workspace remains 3.15.2. [The toolchain guide](../TOOLCHAIN.md) records exact versions, source links, lock refresh and the shared native qualification command.

Snowflake Connector 5.1.0 and snowflake-sqlalchemy 2.1.0 loaded and compiled SQL locally. **No native Snowflake connection or query ran**; DC-014–DC-016 still need the target environment. Full ODCS/GX business-rule mapping, catalogue integration, WSL, resource certification, release publication and enforced review controls remain their own backlog items.
