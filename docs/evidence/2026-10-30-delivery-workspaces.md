# Independent delivery and editor acceptance

Recorded: 2026-10-30 (Europe/Madrid). Machine timestamps below use UTC. This increment adds project registration, host mounts, per-project database identities, scoped reset and generated editor configuration to merged Datacon `62d7582b00779d0acf8c409f9fef69b40101f758`. Runtime input hashes identify the tested working tree; package versions, image digests and the Opharma reference pin are unchanged.

## Native macOS ARM64

`python3.14 scripts/qualify_projects.py --expected-architecture arm64 --output .local/project-qualification/2026-10-30-arm64-final` passed from **2026-10-29 23:04:40 UTC to 23:05:51 UTC**. The new instance was `projects-20261029230440-d2e0ed`. [The complete step record](2026-10-30-delivery-workspaces/arm64-projects/qualification.json) and sanitised transcripts are archived with [runtime identities](2026-10-30-delivery-workspaces/arm64-projects/build-1-identities.json).

- Pinned Opharma in the workspace volume and a separate host Git fixture retained independent histories and original layouts. The host path included both spaces and a dollar sign; reads and writes worked in both directions.
- `dc_opharma` and `dc_sample` passed database/DuckDB/RLS smoke. Both were denied connection, role switching and database deletion against the other project; role creation was denied.
- Reprovisioning preserved both probes. An incorrect reset confirmation failed. Resetting Opharma removed its table while the sample project's value remained `7`.
- Container recreation preserved both dirty checkout snapshots, the sample database value and all credential hashes. Only qualification containers/networks were removed; source trees, local state and volumes remain.
- Opharma ran **35 tests: 34 passed, one expected skip**, plus five ODCS bundles. The independent host fixture's test passed using the platform dependency set.

The core regression command `python3.14 scripts/qualify.py --expected-architecture arm64 --output .local/qualification/2026-10-30-core-projects` also passed **2026-10-29 23:06:40 UTC to 23:08:26 UTC**. [Core results](2026-10-30-delivery-workspaces/arm64-core/qualification.json) record two uncached native builds, identical complete dependency inventories, both `unless-stopped` policies, non-root/database smoke and intentional wheel-hash/OS-inventory failures. Each build passed the Opharma test counts and all **14 checkpoints on initial execution and identical replay**.

Host tests: **41 passed on Python 3.14.8 and 3.12.15**. Compose validation, documentation links and whitespace checks passed. The default instance's workspace/warehouse remained running and healthy, and its original Opharma checkout still had only the retained `.datacon-retention-20261029.txt` uncommitted probe. No retained volumes were removed.

## Actual graphical editor

The real VS Code **1.144.0 ARM64** application, Dev Containers extension **0.469.0** and CLI **0.89.0** opened the generated Opharma editor folder for separate instance `projects-20261029230140-2e22c5`. Its current descriptor was regenerated after the final runtime changes.

The window visibly opened `/workspaces/opharma/pharma-commercial-lab` in the named Dev Container. A new **Datacon project** terminal reported UID **1000**, Python **3.15.2** and database/current user **`dc_opharma:dc_opharma`**. A file was typed, saved, closed and reopened through the graphical editor; its displayed text and container-side SHA-256 matched. [Editor evidence](2026-10-30-delivery-workspaces/editor.json) records the observations and terminal-produced values. The test window and only that instance's containers were closed afterwards; volumes were retained.

The automated project harness deliberately reports `graphical_editor: NOT_EXECUTED`; the separate actual GUI exercise above supplies that evidence. This is an existing Mac installation, not a fresh-machine onboarding trial.

## Native AMD64 CI

Pending the PR run for this increment. Previous core-only AMD64 evidence does not establish the new host-bind and project-reset workflow. The workflow now runs both shared scripts on native `ubuntu-24.04`, with read-only permissions, pinned actions and the existing 30-minute job limit.

## Boundaries

The evidence archive contains reports, hashes, inventories and sanitised command transcripts, excluding credentials, runtime databases and complete fixtures. Trailing whitespace was removed from archived text. The two-project checks use one trusted developer's shared workspace; they establish SQL role separation and scoped lifecycle behaviour, not isolation from a malicious user with access to all mounted secrets.

DC-003's existing-core repository/reset acceptance is implemented. Approved optional dependency environments and immutable release/capability adoption remain with DC-001/DC-007/DC-032. DC-002's clean-machine gate, Windows/WSL acceptance, constrained resource certification, GX, native Snowflake and the full v1 platform remain outstanding. No platform release is claimed.
