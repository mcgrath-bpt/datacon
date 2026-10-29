# Platform and delivery operating model

Recorded: 2026-10-29. This is the clarified direction for Datacon and the first Opharma delivery. Enforcement remains implementation work.

## Shared platform and separate deliveries

Datacon is the common development tooling and standards baseline, owned by the Tech Lead. Developers run their own instances of an approved release. Its evolution should be deliberate and stable while necessary fixes still arrive promptly.

OpenMetadata, its dedicated database/search services and ingestion tooling belong to this platform in v1. The [v1 service inventory](V1_SERVICES.md) defines their lifecycle and resource modes. Projects contribute their metadata and rules through platform-owned integrations; starting a new pipeline does not require its own catalogue deployment.

Project repositories own business logic, contracts, semantics, fixtures, tests and deployment artefacts. They have independent Git histories and release lifecycles. They may depend on each other through explicit data contracts or versioned software interfaces. They do not embed or fork Datacon source to obtain a development environment.

A project can record its approved baseline for reproducibility without becoming part of the platform repository. Keep the binding small: release/image reference and approved capabilities. Optional working-directory and command metadata are configuration, not a second toolchain.

## Developer lifecycle

1. Obtain Datacon and start an approved baseline.
2. Clone or open one or more project repositories inside its persistent workspace.
3. Build or evolve the pipeline, test it and commit/push changes to its project repository.
4. Retain the workspace, including personal experiments and unfinished work, or start a fresh environment for the next task.
5. Before handoff or promotion, reproduce the committed change in clean acceptance using the approved baseline.

Checkouts belong in persistent bind mounts or named workspace volumes. Cloning from inside the container is supported; a host-side clone is not required. Docker volumes persist independently of container replacement. See [Docker's volume lifecycle](https://docs.docker.com/engine/storage/volumes/).

Separate containers per task/project remain an option, not a consequence of having separate repositories. Project data/service identities still need isolation. A fresh workspace must not erase the retained dirty workspace. Clean acceptance must exclude inherited personal packages, virtual environments/node_modules and uncontrolled data; simply restarting the container does not achieve this.

## Personal additions and approved dependencies

Developers may install local tools for exploration. Those additions are personal state, not an accepted prerequisite for someone else's work.

Once a tool, package, version or setup step is needed to build, test, run or support a delivery, the developer raises it with the Tech Lead. The need must be approved or otherwise resolved, with reproducible provision defined in the platform repository before handoff. This applies even when only one project initially needs it.

For example, trying npm locally is allowed. Making Node/npm necessary for a pipeline build requires an agreed platform capability. A project's package manifest/lockfile can record its approved application dependencies; committing that file does not bypass the approval process.

Central ownership does not mean installing every approved tool in every base image. The Tech Lead can approve a platform-owned optional feature/profile or isolated dependency environment. Its definition, versions and provisioning remain centrally versioned and tested. Projects select approved capabilities rather than maintain competing images.

## Adoption and enforcement

Make the approved route convenient: documented bootstrap, released images, clear diagnostics and the same task commands locally and in CI. Define supported releases and a manageable upgrade path so stable does not become indefinitely outdated.

Use clean CI based on the approved release, dependency/configuration-change checks, and required Tech Lead review for baseline and delivery-dependency changes. CODEOWNERS identifies reviewers; required owner approval also needs repository protection/rules. A CODEOWNERS file alone does not prevent merging. See [GitHub's code-owner documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners).

Test enforcement with a deliberate undeclared dependency and an unapproved baseline change. The Tech Lead owns timely decisions and reliable releases; developers own declaring needs and producing reproducible delivery evidence. Local experimentation remains possible while handoff has an enforced standard.

## Snowflake promotion

Datacon is the development environment. Promote the project's versioned code, migrations, contracts, semantic definitions and configuration to Snowflake. Do not promote a developer's modified container as the pipeline.

A library installed in Datacon is not automatically available or supported in Snowflake. Record runtime requirements, resolve them through the same dependency process, and verify target packaging/execution. Deployment evidence binds the project revision and approved baseline. The exact promotion mechanism is part of the early Snowflake work.

## First two repositories

- **Datacon:** Tech Lead-owned baseline, approved dependency provisioning, lifecycle commands, handbook and enforcement controls.
- **Opharma:** first consumer; retain its own code, contracts, semantics, fixtures and history. Reproduce its existing requirements in Datacon, resolve baseline gaps through the Tech Lead, then qualify its Snowflake artefacts.

This method applies to other engineering disciplines. Data-specific tools are capabilities of the baseline; the ownership, reproducibility and delivery model are reusable.
