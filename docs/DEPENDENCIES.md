# From personal experiment to delivery dependency

Recorded: 2026-10-30. The Tech Lead owns all reproducible dependency provision. A tool required to build, test, run, deploy or support a delivery is a delivery prerequisite, even with one consumer. Personal experiments remain local state and must not silently satisfy acceptance.

1. Copy the [dependency request](../.github/dependency_request_template.md) into a focused platform PR or issue. Name the delivery and exact requirement, including its target execution location. Propose the smallest platform-owned capability, exact versions and complete locks rather than a project-owned image.
2. The Tech Lead records approval, rejection or an agreed alternative with a date and review URL. Pending is not approved. Application manifests/lockfiles may remain in the delivery repository, but their tools, packages and target-runtime dependencies need this decision too.
3. Implement approved provision here, normally as an optional finite job or isolated environment. Pin external images by digest and packages/schemas by exact version and hash. Include native architecture evidence, adverse dependency tests, resource impact and an upgrade/removal path. Keep the base workspace small; long-running services use `unless-stopped`, jobs terminate.
4. Qualify the capability from clean inputs, add its exact provision/target/evidence to [the catalogue](../platform/capabilities.json), and publish it through [the release process](RELEASES.md). A successful package import or merged PR is not an immutable release.
5. Adopt the release/capability in the delivery's own reviewed pin and prove its committed pipeline in clean acceptance. Demonstrate that removing the approved capability or substituting a personal-only dependency fails. Preserve dirty retained work and database state while doing so.

Developers own the request and delivery tests. The Tech Lead owns the decision, reproducible provision, compatibility/support policy and target-runtime approval. Platform maintainers collect evidence and maintain the locks; delivery maintainers protect dependency paths and invoke the same acceptance commands locally and in CI. Required review must cover manifests, lockfiles, baseline pins, Docker/Dev Container definitions, installer scripts, target deployment specifications, CI and ownership/policy files. Datacon owns its whole source tree through CODEOWNERS. Equivalent controls in each delivery repository remain a separate activation step.

The existing quality capability illustrates platform provision: DC-007 introduced a separate Python 3.14.8 job because GX/Data Contract CLI exclude workspace Python 3.15. The [merged PR #4](https://github.com/mcgrath-bpt/datacon/pull/4) records its exact versions and both native architectures. Its merge is observed; independent approving review was not enforced at that time. Do not retrospectively label it as such.

## Node/npm acceptance request: pending

**DEP-001 / DC-032**, prepared 2026-10-30. A small independent delivery fixture should require Node/npm to build a deterministic JSON artefact. This exercises the requested experiment-to-delivery process without moving pipeline business logic into Datacon.

- **Need:** demonstrate that an experimental build tool cannot become a shared prerequisite through a delivery lockfile alone.
- **Decision:** **PENDING**; no Node/npm version, image or packages have been approved or installed by this increment.
- **Proposed provision:** an optional non-root, finite platform-owned Node job, pinned by multi-platform image digest; npm version verified from the image. Keep the current workspace unchanged. Choose the exact stable supported version and verify upstream hashes when the Tech Lead approves the requirement.
- **Application dependency:** prefer a dependency-free fixture initially, using npm scripts and a committed lockfile; any third-party package needs an explicit exact dependency decision and integrity lock.
- **Clean use:** a separate committed fixture checkout, disposable job home/output and no retained `node_modules`, global npm installs or host package paths. Run on native ARM64 and AMD64 and compare deterministic output. Keep the fixture's history independent.
- **Negative cases:** the current release verifier rejects `node-npm`; a personal-only installation cannot make the approved clean job pass; a changed baseline/pin cannot merge without required checks and, after activation, owner approval.
- **Native targets:** this build capability would not approve Node or npm inside Snowflake. Any procedure/UDF/container target package must separately declare its runtime, supported version, installation/channel permissions, lock and actual native execution evidence.
- **Remaining evidence:** Tech Lead decision, exact pins/provision, both native runs, immutable release, delivery adoption and remote review rejection. The host negative test is useful evidence for the pin boundary; it is not completion of this process.

No unrequested dependency is introduced solely to make the backlog appear complete. DC-032 remains open until the approved example and remote enforcement have been demonstrated.
