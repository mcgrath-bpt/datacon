# Contributing to Datacon

Datacon is the Tech Lead-owned platform baseline. Read [the operating model](docs/OPERATING_MODEL.md), [the plan](PLAN.md) and [the backlog](BACKLOG.md) before changing it. Pipeline business logic belongs in its independent project repository.

## Initial repository bootstrap

Verified: 2026-10-29. The user created local Git history with initial commit `601cee3` (`chore: establish Datacon platform plan and repository conventions`) on `main`. The canonical public repository is [mcgrath-bpt/datacon](https://github.com/mcgrath-bpt/datacon), configured as `origin` at `https://github.com/mcgrath-bpt/datacon.git`. Continue this history; do not initialise a second repository.

On resumption, approved Git writes created `feat/DC-002-core-runtime` while preserving the working tree. Docker and GitHub access also succeeded with approval. The default sandbox still protects Git metadata and the Docker socket; use the session approval mechanism when needed and recheck access in each new session. No repository ownership repair or permission change through `chmod` is indicated. [HANDOVER.md](HANDOVER.md) records the current state.

The user supplied this remote on 2026-10-29. Its initial commit `6b955ac` contains the MIT licence and was merged with the local design history, preserving both roots. `main` now includes the merged core implementation (`dd2989c`); `feat/DC-007-core-locks-ci` carries the next dependency-lock and CI increment. The previous feature branch is retained. Use ordinary pushes and preserve remote history. `.gitignore` excludes common local secrets, environments, outputs and delivery checkout directories; inspect staged files before committing.

## Normal change workflow

1. Select or update a stable `DC-XXX` backlog item and its acceptance criteria.
2. Create a focused branch from current `main`, for example `feat/DC-002-core-runtime` or `docs/DC-006-onboarding`.
3. Implement the change and update its documentation. Declare any dependency change to the Tech Lead before it becomes a delivery prerequisite.
4. Review the diff, run `git diff --check`, and execute checks appropriate to the change. `./datacon check` runs host tests and `./datacon config` validates Compose without a daemon. For runtime changes, follow [the core quick-start](docs/CORE_QUICKSTART.md) and [shared qualification procedure](docs/CORE_LOCKS.md), and record actual versions, host architecture and execution evidence.
5. Commit the reviewed files. Use a short imperative subject explaining the change; include the backlog ID in subsequent implementation commits or the PR.
6. Open a PR using the template. Record validation, unavailable environments and any compatibility or migration impact.

Do not mark a backlog item done until its acceptance criteria have evidence. For early implementation, distinguish a working core increment from the complete v1 platform, which includes OpenMetadata and project metadata/quality publication.

## Review and release policy

The Tech Lead reviews baseline, dependency and release changes. Required checks and review protection must be configured on the remote before claiming enforcement; written conventions alone do not enforce them. The exact reviewer account/team and repository settings remain to be established in DC-001/DC-032.

The initial documentation commit is not a runtime release. Under DC-007, record and qualify exact image and tool versions. Under DC-001, publish an immutable release reference, supported hosts/capabilities, compatibility notes and upgrade guidance. A project records the approved Datacon release used for acceptance; platform and project histories remain separate.

See [the working guide](docs/WORKING_GUIDE.md) for evidence, secrets, clean acceptance, date formatting and daily delivery conventions.
