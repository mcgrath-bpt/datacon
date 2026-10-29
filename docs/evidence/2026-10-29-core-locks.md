# Core lock and CI qualification

Recorded: 2026-10-29. Scope: DC-007's existing core dependency set. This is not a qualified v1 release and DC-007 remains open.

## Synchronisation and inputs

Local `main` was fast-forwarded to `dd2989c5d866e69669e0804a183832d825bc1756` and `feat/DC-007-core-locks-ci` created. `git diff origin/main feat/DC-002-core-runtime` was empty before implementation. The previous feature branch is retained. [Opharma's merge comparison](https://github.com/mcgrath-bpt/opharma/compare/b43c6897f6bdda2adcf60fc468fe8aaff31f52eb...f1d68d01e6659ba3b279b98afbb9538cbece7473) has no changed files and both revisions have tree `a876facad605a7718785a45be8ada531a3cf8ff5`. The reference pin now selects the merge.

Python 3.15.2, all six dependency versions and both base image digests are unchanged. All seven selected wheels were downloaded from their published PyPI URLs; their independently calculated SHA-256 values matched [the provenance manifest](../../requirements/workspace-wheels.json). Dated archive inputs and 131-package workspace inventories for each architecture are recorded in [the lock procedure](../CORE_LOCKS.md). AMD64 inventory preparation used emulation on this Mac; that preparation alone is not native qualification.

## Native ARM64 results

Executed `python3.14 scripts/qualify.py --expected-architecture arm64 --output .local/qualification/core-locks-arm64` from 2026-10-29 22:32:11 UTC to 22:33:43 UTC. [The machine report](2026-10-29-core-locks/arm64/qualification.json) records the working tree and SHA-256 of implementation/lock inputs because this run preceded the implementation commit.

- Two `--pull --no-cache` workspace builds passed; installed workspace OS, warehouse OS and Python dependency inventories were identical. Image IDs were recorded, not required to match.
- Workspace Python 3.15.2, UID 1000; PostgreSQL 17.7, SQL extension 1.1.0. `pip check`, the complete OS lock, non-superuser forced RLS and an observed `DuckDBScan` passed in both runs. Both services used `unless-stopped`.
- Each reference run tested merge `f1d68d01e6659ba3b279b98afbb9538cbece7473`: 35 tests run, 34 passed, one expected static-workbook skip. All 14 checkpoints passed initially and on replay; every database table retained the same row multiset. Five ODCS bundles validated.
- A modified OS lock failed the actual Dockerfile gate with `OS inventory mismatch`; a deliberately incorrect wheel hash failed pip's hash check. Network errors or unrelated failures cannot satisfy these checks.
- 31 host tests passed on Python 3.14.8 and separately on 3.12.15. Compose validation, local Markdown links, workflow YAML parsing, shell syntax and whitespace checks passed.
- Only qualification instance `qual-20261029223211-e63f2e99` was stopped. Its volumes and credentials remain. Both default containers remained healthy; the retained checkout stayed at `b43c6897f6bdda2adcf60fc468fe8aaff31f52eb` with `?? .datacon-retention-20261029.txt` unchanged.

Selected inspectable evidence: [doctor](2026-10-29-core-locks/arm64/doctor.txt), [first inventory](2026-10-29-core-locks/arm64/build-1-inventories.json), [second inventory](2026-10-29-core-locks/arm64/build-2-inventories.json), [first image identities](2026-10-29-core-locks/arm64/build-1-identities.json), [second image identities](2026-10-29-core-locks/arm64/build-2-identities.json), [initial Opharma report](2026-10-29-core-locks/arm64/build-1-opharma-first-run.json), [replay](2026-10-29-core-locks/arm64/build-1-opharma-replay.json), [second reference summary](2026-10-29-core-locks/arm64/build-2-opharma-summary.json), [OS rejection](2026-10-29-core-locks/arm64/reject-os-inventory.txt), [wheel rejection](2026-10-29-core-locks/arm64/reject-wheel-hash.txt). Sanitised build/smoke/test transcripts are stored alongside them, with trailing whitespace normalised for Git. No credentials, database files, full fixtures or delivery checkouts are included.

## Native AMD64 CI

[Native AMD64 run 40967301222](https://github.com/mcgrath-bpt/datacon/actions/runs/40967301222) passed on `ubuntu-24.04`. PR head: `1bd679f2f753dae15dda78f56d025bfea39ba119`; GitHub tested merge revision: `f481455100a6517246d6adf97ed0cc817c9aae91`. Qualification ran from 2026-10-29 22:37:45 UTC to 22:39:51 UTC. [Run and artefact metadata](2026-10-29-core-locks/ci-run.json) bind the source and uploaded evidence.

- Native Linux/x86_64 host and daemon; host Python 3.12.3, Docker 28.0.4, Compose 2.38.2. Workspace Python 3.15.2, UID 1000, pip 26.2.2. No emulation was used.
- Both uncached builds passed with identical workspace OS, warehouse OS and Python inventories. The complete 131-package AMD64 workspace lock matched. Smoke, `pip check`, both restart policies and both deliberate integrity failures passed.
- Each build passed 34 Opharma tests with one expected skip and all 14 initial/replay checkpoints, with identical database row multisets. All 31 host tests passed.
- The evidence upload passed: artefact `core-amd64-40967301222-1`, ID `12938910937`, 81,352 bytes. Downloaded ZIP SHA-256 matched GitHub's digest `21b80e561d57f747bf26633568ac8fc47c50204acb35f014a217f9866dfc7a50`. Its 52 members were all named JSON/text reports/transcripts; selected reports are committed here so they outlive the 30-day CI retention period.

Inspect [qualification](2026-10-29-core-locks/amd64/qualification.json), [doctor](2026-10-29-core-locks/amd64/doctor.txt), [first inventory](2026-10-29-core-locks/amd64/build-1-inventories.json), [second inventory](2026-10-29-core-locks/amd64/build-2-inventories.json), [first identities](2026-10-29-core-locks/amd64/build-1-identities.json), [second identities](2026-10-29-core-locks/amd64/build-2-identities.json), [initial checkpoints](2026-10-29-core-locks/amd64/build-1-opharma-first-run.json), [replay](2026-10-29-core-locks/amd64/build-1-opharma-replay.json) and [second reference summary](2026-10-29-core-locks/amd64/build-2-opharma-summary.json).

The workflow covers pull requests, pushes to `main` and manual dispatch. Actions are SHA-pinned, repository permissions are read-only, the job timeout is 30 minutes, and sanitised evidence is uploaded on success or failure. The qualification step has a 27-minute limit to reserve upload time.

## Remaining boundaries

GX/SQLAlchemy/Snowflake dependencies, native cloud integration, WSL, graphical editor acceptance, resource-envelope certification, the full RLS/concurrency matrix, branch protection and release publication remain separate work. Signed snapshots deliberately freeze updates; advancing them requires reviewed locks and repeated native acceptance. CI presence does not establish enforced merge protection.
