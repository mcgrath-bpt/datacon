# Opharma as the first delivery reference

Reviewed on 2026-10-29: [PR #1 — Adopt ODCS contracts, recurring S1–S5 model and Power BI TMDL](https://github.com/mcgrath-bpt/opharma/pull/1).

Inspected head: `b43c6897f6bdda2adcf60fc468fe8aaff31f52eb`, branch `feat/odcs-pharma-operations-tmdl`. The PR was open when initially inspected. It has since merged as `f1d68d01e6659ba3b279b98afbb9538cbece7473`; the merge has the same tree as the tested head. `platform/reference.json` now selects that merge commit. The retained dirty checkout remains on the earlier head.

This review read the PR description, root and nested READMEs, operating guide, acceptance scenarios, existing backlog, dependency file, selected Snowflake runner code and Power BI binding plan. It did not run the project or validate any live target. The upstream repository and PR were not changed.

## What is already available

The PR supplies an implementation under `pharma-commercial-lab/`, with ODCS 3.1 JSON bundles for source, canonical, pipeline, consumption and visualisation concerns. It includes a Python/SQLite reference, immutable synthetic deliveries, independent expected results, Snowflake assets and enterprise integration handoffs. Retain these artefacts in their delivery repository rather than importing their implementation into Datacon.

The root README reports 35 tests with 34 passing and one skipped, reconciliation at 14 checkpoints, and 756 passing quality assertions. These are prior recorded results, not executions performed during this planning task. DC-008 must reproduce them and explain any differences. The same README distinguishes expected source-quality alerts from failures of the acceptance logic. See the [pinned project README](https://github.com/mcgrath-bpt/opharma/blob/b43c6897f6bdda2adcf60fc468fe8aaff31f52eb/README.md).

The dependency file declares `jsonschema==4.26.0`; the reference does not already depend on GX or Soda. Qualify GX alongside the existing validators before replacing anything. See [requirements-dev.txt](https://github.com/mcgrath-bpt/opharma/blob/b43c6897f6bdda2adcf60fc468fe8aaff31f52eb/pharma-commercial-lab/requirements-dev.txt).

## Use cases to carry into the backlog

| Scenario | Meaning that must survive adaptation | Main work items |
| --- | --- | --- |
| S1: engagement and consent | Resolve identities unambiguously; use consent at reporting cutoff; distinguish identity-rate alerts from consent exceptions | DC-008, DC-013, DC-021 |
| S2: activity and product | Customer/product/day grain; current product hierarchy; avoid inflating quality denominators through multi-product joins | DC-013, DC-015, DC-017 |
| S3: customer and territory | Effective intervals, latest effective assignment, retained missing assignments and hard failures for unresolved conflicting ties | DC-012, DC-017, DC-021 |
| S4: late arrivals and corrections | Preserve the latest accepted version; enforce lateness boundaries; apply tombstones; rejected records cannot replace trusted state | DC-012, DC-015, DC-017 |
| S5: campaign effectiveness | Preserve zero-contact members, campaign-to-date meaning, per-campaign quality scope and the latest completed Monday publication | DC-013, DC-021, DC-022 |

The accepted business definitions are in [PUBLIC_ACCEPTANCE.md](https://github.com/mcgrath-bpt/opharma/blob/b43c6897f6bdda2adcf60fc468fe8aaff31f52eb/pharma-commercial-lab/docs/PUBLIC_ACCEPTANCE.md). Some older crawl documentation describes an earlier runtime state. Use the recurring implementation's operating guide and actual tests when reconciling implementation status; preserve business semantics unless an explicit change is agreed.

## Operational behaviours worth reusing

Source manifests bind exact files, hashes and contract identities. Ordered batches, replay, rollback/repaired retry, registry binding and separate business-effective versus delivery-visible time make useful platform conformance cases. The fixture includes reference changes, identity issues, corrections and deletions rather than only clean append-only input.

ODCS bundles are authoring units, not one-table constraints. Keep multi-object identity and snapshot-qualified keys. The project uses JSON and a vendored schema, so Datacon must accept those directly. Source schema editions, contract versions and release IDs are distinct.

Preserve the distinction between hard publication gates and alertable exceptions. The reference uses logical time; that cannot demonstrate real completion deadlines or notification delivery. The [ODCS operating guide](https://github.com/mcgrath-bpt/opharma/blob/b43c6897f6bdda2adcf60fc468fe8aaff31f52eb/pharma-commercial-lab/docs/ODCS_OPERATIONS.md) supplies these operating conventions.

## Semantic and agent implications

The current semantic output is Power BI/Analysis Services TMDL, including seven semantic tables and 16 measures in the binding plan. Keep its scenario facts independent and preserve scorecard scope/history guards and daily-versus-Monday sources. Add Snowflake Semantic Views as another native target with shared business tests.

The binding plan explicitly reports static contract-binding validation and no import. Native TOM parsing, DAX compilation, refresh and access checks remain work. CSV parity is not equivalent to successful Power BI deployment. See [visualization-plan.json](https://github.com/mcgrath-bpt/opharma/blob/b43c6897f6bdda2adcf60fc468fe8aaff31f52eb/pharma-commercial-lab/integrations/powerbi/visualization-plan.json).

The independent reference/evaluator distinction is valuable for agent-built pipelines. For that benchmark, provide a filtered source-only workspace and keep truth generation/expected outputs outside the builder's mounts and credentials. Do not assume isolation merely because the code is in a separate directory.

## Native work still required

Prioritise the existing S2/S4 Snowflake path, then S3 and S1/S5. The existing runner accepts a named connection, stage, schema and bounded checkpoint range and records exports/query IDs; qualify and reuse it. See [run_operations_snowflake.py](https://github.com/mcgrath-bpt/opharma/blob/b43c6897f6bdda2adcf60fc468fe8aaff31f52eb/pharma-commercial-lab/src/run_operations_snowflake.py).

Live Snowflake/stage execution, real scheduling/deadlines, notification delivery and tenant-specific governance/access behaviour remain native acceptance requirements. Preserve Collibra, Ataccama and Immuta handoffs even when the local quality engine is GX. The upstream backlog already records target acceptance work; Datacon's backlog links to it conceptually without changing its statuses. See the [existing delivery backlog](https://github.com/mcgrath-bpt/opharma/blob/b43c6897f6bdda2adcf60fc468fe8aaff31f52eb/pharma-commercial-lab/TODO.md).
