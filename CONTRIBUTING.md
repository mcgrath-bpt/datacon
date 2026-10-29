# Contributing to Datacon

Datacon is the Tech Lead-owned platform baseline. Read [the operating model](docs/OPERATING_MODEL.md), [the plan](PLAN.md) and [the backlog](BACKLOG.md) before changing it. Pipeline business logic belongs in its independent project repository.

## Initial repository bootstrap

Recorded: 2026-10-29. This workspace contains the design and repository conventions. The coding session attempted `git init -b main`, but filesystem permissions rejected creation of `.git` with `Operation not permitted`. No initial commit or remote has been created by the session.

Run the following from a normal terminal with write access to this folder. These commands are for the initial, currently uninitialised workspace; if someone has already created history, inspect it and continue that history instead.

```sh
cd /Users/mmcgrath/Documents/dev/00-base/datacon
git init -b main
git add .gitignore .gitattributes .editorconfig AGENTS.md CONTRIBUTING.md README.md PLAN.md BACKLOG.md docs/WORKING_GUIDE.md docs/OPHARMA_REFERENCE.md docs/OPERATING_MODEL.md docs/V1_SERVICES.md .github/pull_request_template.md
git diff --cached --check
git diff --cached --stat
git diff --cached
git commit -m "chore: establish Datacon platform plan and repository conventions"
git status --short --branch
git log -1 --format='%h %s'
```

Inspect the staged content before committing. The explicit path list includes the current platform documents and repository conventions. `.gitignore` excludes common local secrets, environments, outputs and delivery checkout directories; it cannot identify every possible secret.

Once the commit exists, update the current-state notes in README and DC-001 with the observed commit reference. Agree the GitHub owner, repository name and visibility, then configure `origin` and push. A lookup of `mcgrath-bpt/datacon` through the connected GitHub account returned 404; that does not establish whether the repository is absent or inaccessible. No remote is assumed.

## Normal change workflow

1. Select or update a stable `DC-XXX` backlog item and its acceptance criteria.
2. Create a focused branch from current `main`, for example `feat/DC-002-core-runtime` or `docs/DC-006-onboarding`.
3. Implement the change and update its documentation. Declare any dependency change to the Tech Lead before it becomes a delivery prerequisite.
4. Review the diff, run `git diff --check`, and execute checks appropriate to the change. For documentation, verify local links and examples. For runtime changes, record actual versions, host architecture and execution evidence.
5. Commit the reviewed files. Use a short imperative subject explaining the change; include the backlog ID in subsequent implementation commits or the PR.
6. Open a PR using the template. Record validation, unavailable environments and any compatibility or migration impact.

Do not mark a backlog item done until its acceptance criteria have evidence. For early implementation, distinguish a working core increment from the complete v1 platform, which includes OpenMetadata and project metadata/quality publication.

## Review and release policy

The Tech Lead reviews baseline, dependency and release changes. Required checks and review protection must be configured on the remote before claiming enforcement; written conventions alone do not enforce them. The exact reviewer account/team and repository settings remain to be established in DC-001/DC-032.

The initial documentation commit is not a runtime release. Under DC-007, record and qualify exact image and tool versions. Under DC-001, publish an immutable release reference, supported hosts/capabilities, compatibility notes and upgrade guidance. A project records the approved Datacon release used for acceptance; platform and project histories remain separate.

See [the working guide](docs/WORKING_GUIDE.md) for evidence, secrets, clean acceptance, date formatting and daily delivery conventions.
