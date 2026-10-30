# Contributing to Datacon

Datacon is the Tech Lead-owned platform baseline. Read [the operating model](docs/OPERATING_MODEL.md), [the plan](PLAN.md) and [the backlog](BACKLOG.md) before changing it. Pipeline business logic belongs in its independent project repository.

## Initial repository bootstrap

Verified: 2026-10-29. The user created local Git history with initial commit `601cee3` (`chore: establish Datacon platform plan and repository conventions`) on `main`. The canonical public repository is [mcgrath-bpt/datacon](https://github.com/mcgrath-bpt/datacon), configured as `origin` at `https://github.com/mcgrath-bpt/datacon.git`. Continue this history; do not initialise a second repository.

On resumption, approved Git writes created `feat/DC-002-core-runtime` while preserving the working tree. Docker and GitHub access also succeeded with approval. The default sandbox still protects Git metadata and the Docker socket; use the session approval mechanism when needed and recheck access in each new session. No repository ownership repair or permission change through `chmod` is indicated. [HANDOVER.md](HANDOVER.md) records the current state.

The user supplied this remote on 2026-10-29. Its initial commit `6b955ac` contains the MIT licence and was merged with the local design history, preserving both roots. `main` now includes the core implementation and dependency-lock/CI increment (`62d7582`). `feat/DC-003-delivery-workspaces` adds the independent delivery workflow. The previous feature branch is retained. Use ordinary pushes and preserve remote history. `.gitignore` excludes common local secrets, environments, outputs and delivery checkout directories; inspect staged files before committing.

## Normal change workflow

1. Select or update a stable `DC-XXX` backlog item and its acceptance criteria.
2. Create a focused branch from current `main`, for example `feat/DC-002-core-runtime` or `docs/DC-006-onboarding`.
3. Implement the change and update its documentation. Declare any dependency change to the Tech Lead before it becomes a delivery prerequisite.
4. Review the diff, run `git diff --check`, and execute checks appropriate to the change. `./datacon check` runs host tests and `./datacon config` validates Compose without a daemon. For runtime changes, follow [the core quick-start](docs/CORE_QUICKSTART.md) and [shared qualification procedure](docs/CORE_LOCKS.md), and record actual versions, host architecture and execution evidence. Changes to project mounts, credentials or lifecycle also require `python3 scripts/qualify_projects.py --expected-architecture <arm64|amd64>`; follow [the delivery guide](docs/DELIVERY_WORKSPACES.md) for separate graphical acceptance.
5. Commit the reviewed files. Use a short imperative subject explaining the change; include the backlog ID in subsequent implementation commits or the PR.
6. Open a PR using the template. Record validation, unavailable environments and any compatibility or migration impact.

Do not mark a backlog item done until its acceptance criteria have evidence. For early implementation, distinguish a working core increment from the complete v1 platform, which includes OpenMetadata and project metadata/quality publication.

## Review and release policy

The Tech Lead reviews baseline, dependency and release changes. [Release and repository controls](docs/RELEASES.md) define reproducible required checks and the separately deferred owner-review rules. The user deferred a second account on 2026-10-30; CODEOWNERS names `mcgrath-bpt`, but required owner approval is not active. Written conventions alone do not enforce review. Use [the dependency process](docs/DEPENDENCIES.md) for new or changed delivery prerequisites, including native target packages.

The initial documentation commit is not a runtime release. Under DC-007, record and qualify exact image and tool versions. Under DC-001, prepare a content-bound manifest from a clean committed checkout, qualify that revision and publish an approved immutable release through the documented process. A project records the release, commit, manifest SHA-256 and selected capabilities in its own reviewed pin; platform and project histories remain separate. No approved release is published yet.

See [the working guide](docs/WORKING_GUIDE.md) for evidence, secrets, clean acceptance, date formatting and daily delivery conventions.
