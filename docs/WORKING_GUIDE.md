# Working with Datacon

Status: proposed team conventions and onboarding route. The [core implementation](CORE_QUICKSTART.md) has ARM64 runtime/reference/persistence evidence; independent new-joiner acceptance remains to be exercised.

## What belongs where

| Platform repository | Delivery repository | Local or external state |
| --- | --- | --- |
| Container image, toolchain, adapters, project-manifest schema, common CI commands, handbook and platform tests | Business requests, ODCS contracts, SQL/Python pipelines, native semantic models, project tests, synthetic fixtures, deployment templates and release pin | Credentials, machine-specific checkout paths, caches, runtime databases, bulky execution evidence and cloud resources |

Commit small, stable evidence summaries and immutable links/checksums; retain full execution artefacts in the project's chosen store or ignored output directory. Never replace a recorded execution result with an assertion that a file exists.

Each delivery remains a separate Git repository. Start the shared Datacon baseline and clone or open one or more delivery repositories inside its persistent workspace; host-mounted checkouts and isolated task containers are also supported. The Tech Lead owns baseline releases and dependency decisions. See the [operating model](OPERATING_MODEL.md).

Personal experimental installs are permitted. Any tool/package/version required by another developer, CI or the delivery must first be agreed with the Tech Lead and provisioned reproducibly through the platform repository. This applies even for a single project. Project lockfiles describe approved application dependencies; they do not replace that approval. The platform may provide optional features or isolated environments to avoid enlarging the default image.

## First-day route

The target onboarding exercise is:

1. Check the documented host/container prerequisites. On Windows, clone into the WSL Linux filesystem and record the WSL package and distribution versions.
2. Obtain Datacon at the approved release and start a fresh baseline. Read its working rules and supported tool versions.
3. Clone or open the delivery repository inside the persistent workspace, select its working directory and confirm its identity. A host-side checkout is optional; several projects can share the workspace.
4. Run the doctor/preflight task, then the reference contract and fixture tests. Start the database only for tasks that need it.
5. Inspect a contract, a transformation, a semantic definition and the resulting evidence for one use case.
6. Make an intentional bad-data change in a disposable fixture and observe the expected failure. Restore it and verify the passing path.
7. Make a small requested delivery change, run affected checks, and prepare a PR that links the requirement, contract and evidence.
8. Run native Snowflake checks when configured; otherwise report their unverified status. The full catalogue is not an onboarding prerequisite.

DC-006 requires this exercise to be performed by someone new to the project. The core quick-start documents the first implemented commands and their verification limits; the complete team exercise remains an acceptance target.

## Daily delivery method

Start with the business question and intended output grain. Identify approved sources, keys, joins, effective/arrival-time rules, corrections/deletions, quality thresholds and access intent. Resolve missing meaning with the responsible owner; do not guess it from column names.

Update the source contract or semantic definition first when the requirement changes. Generate supported artefacts deliberately and inspect the diff. Keep target-specific SQL, DAX and access policies explicit. Database DDL generation does not author a safe migration automatically.

Use a delivery feature branch. Keep changes focused and include relevant fixture cases for altered behaviour. Run the smallest meaningful checks first, followed by the affected local integration and native-target checks. Test adverse paths such as replay, empty data, ambiguous identity and failed publication when they are relevant to the change.

For a PR, explain the concrete behaviour before and after, why it changed, the contract/semantic impact, the validation performed, and remaining target limitations. Do not mix a business-rule change with unexplained dependency upgrades. Review generated changes alongside their source definitions.

Publish only complete, validated snapshots according to the project's policy. Distinguish expected business alerts, hard quality failures, execution errors and no-data outcomes. Keep the source manifest, contract hash, code revision and target query IDs with the run evidence.

## Versioning and upgrades

Record the approved Datacon release/image used for the delivery. The Tech Lead owns upgrade and supported-release policy; adoption receives compatibility checks. Keep the project binding small and avoid floating tags, implicit startup upgrades or project-owned platform forks. Declare inter-project dependencies through versioned code/data interfaces rather than another developer's checkout paths.

Treat changed keys, grains, metric meaning, policy and publication cadence as potentially breaking changes, even if the columns remain identical. Review a migration or rebuild plan before changing published state. Keep generated artefacts reproducible from committed inputs.

Keep curated synthetic fixtures in Git. Use immutable references for larger datasets. Store credentials outside Git and supply only the selected project's connections to its runtime. The container should not require a mount of the developer's entire home directory.

## Troubleshooting and recovery

Begin with doctor output, service readiness and the failed step's structured report. Identify the platform version, delivery commit, project name, input release and contract fingerprint before comparing two runs.

Resume retains chosen personal work and installed experiments. Fresh starts a clean approved baseline in an isolated task workspace without deleting retained checkouts. Keep code on persistent storage rather than only in a disposable container layer. A clean acceptance run uses a committed revision and excludes inherited personal packages, virtual environments/node_modules and uncontrolled data state; a restart alone is not sufficient.

Normal stop/start preserves volumes. A destructive reset must be explicit and scoped to the named project; never use a global Docker prune as ordinary recovery. CI must reproduce delivery without personal additions, and required Tech Lead review must cover changes to baseline/dependency requirements. These enforcement controls are tracked in DC-032/DC-033.

Keep failure evidence. Repair the cause and rerun against the appropriate immutable inputs. Do not edit a previously published input or make a failed check green by removing it.

## Using agents

An agent receives the same approved business definitions, project rules and deterministic commands as a developer. It should produce a plan, a reviewable code change and test evidence. Missing requirements and unsupported operations must remain visible.

During independent evaluation, the builder cannot receive the hidden expected results or oracle data. Normal developer workspaces and evaluation workspaces have different mounts; a full repository checkout is not a valid hidden-answer boundary.

Reviewers retain responsibility for meaning, changes to acceptance rules, merge and deployment. A successful visible example is not enough to approve a general pipeline generator.

Use British English in team-facing documentation and responses. Prefer “indifferent” when describing freedom of choice.

Use ISO dates in `YYYY-MM-dd` format, for example `2026-10-29`. Where a time is needed, include 24-hour time with seconds: `YYYY-MM-dd HH:mm:ss`. State the timezone or UTC offset when it matters. Machine-readable timestamps should use ISO 8601 with an explicit offset or `Z`, for example `2026-10-29T08:30:00Z`.

“Test yourself, before you wreck yourself.”
