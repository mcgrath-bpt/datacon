# Platform releases and delivery adoption

Recorded: 2026-10-30. DC-001/DC-032 introduce release preparation and verification. There is **no published approved release yet**. The initial proposed release is a **0.1.0 core preview**, not Datacon v1. [The catalogue](../platform/capabilities.json) describes existing technically qualified capabilities; qualification alone is not delivery approval.

## Identity and support

A release comprises an exact `vMAJOR.MINOR.PATCH` (or `-rc.N`) tag, its 40-character Git commit, and a `datacon-release.json` asset. The asset binds the commit/tree, runtime-input SHA-256, exact input hashes, capability catalogue, host evidence and limitations. Version names and moving branches alone are insufficient adoption pins. GitHub release immutability must be enabled before publication: its signed attestation binds the assets and tag, which become immutable when published. See [GitHub's immutable-release behaviour](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases).

The first release uses reproducible source builds from the pinned commit and existing digest/hash locks. It does not claim published Datacon OCI images. Base/warehouse image digests and complete dependency locks remain in the source manifest. Record the actual built image IDs in acceptance evidence; do not present those local image IDs as registry digests. If registry images are introduced, publish multi-platform images by digest and qualify them before adding them to the release manifest.

Before 1.0, a minor release may change interfaces; a patch preserves documented commands, project bindings and retained data. From 1.0, breaking changes require a major version. Every release states supported capabilities/targets, dependency changes, migration/recovery and remaining limitations. The Tech Lead supports the latest approved minor line and the preceding minor line for 30 days after its successor is published. Security fixes may require a documented earlier upgrade; announce the deadline and reason in the release notes. No unattended upgrade or data migration is permitted. Release candidates are opt-in evaluations with no production support commitment.

Current evidence is from an existing macOS ARM64/Docker Desktop host and native Linux AMD64 CI. Actual Windows/WSL, fresh-machine onboarding, the 4-GiB/two-vCPU allocation, native Snowflake and OpenMetadata remain unqualified. OpenMetadata and project integration remain required before v1. Local Snowflake connector imports/SQL compilation do not qualify packages inside Snowflake.

## Prepare and publish

1. Obtain Tech Lead review of dependency decisions, the capability catalogue, compatibility notes and qualification evidence. Merge through the normal PR route. The deferred reviewer configuration below must be resolved before claiming enforced review.
2. Use a clean checkout of the exact release commit. Run host tests and appropriate native qualification on ARM64 and AMD64; retain sanitised evidence tied to that commit/runtime fingerprint. Do not reuse old runtime evidence after runtime inputs change. Write final release notes with the scope and explicit unsupported targets.
3. Prepare the asset outside the checkout or under ignored local state:

   ```sh
   ./datacon release catalogue
   ./datacon release candidate --version 0.1.0-rc.1 --output /tmp/datacon-release.json
   ```

   Candidate generation refuses dirty source, untracked files and ignored runtime overlays. It is deterministic and refuses to overwrite an existing file. It does not execute native qualification, attest the result or grant approval.
4. Audit the remote with `python3 scripts/repository_rules.py`. Inspect the audit before publication. Under the user-approved interim administrator arrangement, the deferred owner-review result is not a blocker; record that exception explicitly in the release decision. Confirm the two required native jobs and governance check succeeded for the release revision. Create a draft GitHub release at that exact commit, attach the manifest and sanitised qualification evidence, and inspect the complete draft. Keep credentials, database files and delivery checkouts out of release assets.
5. The Tech Lead approves the concrete draft and publishes it. GitHub creates the immutable release attestation. Verify the published asset with `gh release verify-asset <tag> /tmp/datacon-release.json --repo mcgrath-bpt/datacon`, and inspect the immutable flag and tag commit. Publication is a separate action; no Datacon command performs it implicitly. Corrections require a new release/version. Titles and release notes can still change, so security/compatibility decisions belong in the pinned manifest/source too.

Administrative release verification currently uses GitHub CLI 2.102.0, observed on this host; a CLI supporting `release verify-asset` is required. It is not a delivery-container prerequisite. The [GitHub CLI manual](https://cli.github.com/manual/gh_release_verify-asset) describes asset verification.

## Independent delivery pin

A delivery commits a small `datacon.lock.json` through its own reviewed PR. It stores identity and requested capabilities only; it does not copy Datacon source or add a competing toolchain. Example shape (replace the explicit placeholders with actual reviewed release values):

```json
{
  "schema_version": 1,
  "repository": "mcgrath-bpt/datacon",
  "release": "v0.1.0-rc.1",
  "commit": "<40-character platform commit>",
  "manifest_sha256": "<SHA-256 of the published manifest bytes>",
  "target": "local-linux-arm64",
  "capabilities": ["workspace-python", "postgres-duckdb", "quality-contracts"]
}
```

Use `local-linux-amd64` for the native AMD64 container runtime. The host evidence remains separate. Retrieve the manifest from the named immutable release, check out Datacon at the pinned commit in its own checkout, then run:

```sh
./datacon release verify --manifest /tmp/datacon-release.json --pin /path/to/delivery/datacon.lock.json
```

The command checks the reviewed digest, exact checkout identity, catalogue/policy, requested capabilities and target, then verifies immutable publication, the signed asset attestation and remote tag commit. Any failed gate exits non-zero. `--offline` runs only the content checks and returns `CONTENT_ONLY`; it cannot satisfy release publication or delivery approval. A malicious or unreviewed delivery pin is not a trust root: protect the delivery's pin, lockfiles, CI and dependency manifests with Tech Lead ownership and required review.

`doctor` continues to show an unreleased checkout as development. Readiness and a matching runtime fingerprint are not release approval. Release verification does not execute the delivery, exclude personal package overlays from its runtime or certify its business outputs; the full clean-execution boundary remains DC-033.

For upgrades, review the release notes and pin diff, select the new commit in a separate platform checkout, and run the project's committed revision in a uniquely named acceptance instance. Preserve the retained instance and its credentials. Promote the delivery pin only after its tests, capability/target checks and migration evidence pass. Roll back by selecting the previous reviewed pin and matching retained state. If a migration changes data incompatibly, restore a tested backup into a new scoped instance; never point older code at incompatible data or reset another project.

## Repository controls and deferred reviewer

[The required-check rules](../governance/github-main.json) require PRs, resolved review threads and up-to-date `core-amd64`, `toolchain-amd64` and `governance` checks from the observed GitHub Actions application ID **15368**. They deny branch deletion and force pushes for ordinary contributors. On 2026-10-30 the user added repository administrators (role ID 5) with `always` bypass; this accepted interim exception also permits bypassing PR and CI requirements. Continue using tested PRs for routine changes. Apply and read back this configuration with:

```sh
python3 scripts/repository_rules.py --apply
```

This also enables immutability for future releases. The command intentionally exits non-zero until **both** rulesets and release immutability match. Under the user-approved interim administrator arrangement, a missing owner-review rule is a reported limitation, not an operational blocker; other mismatches still require investigation. It does not delete unrelated rulesets.

The user deferred creating a second account on 2026-10-30 and subsequently accepted administrator bypass so work can proceed without that account. Required approvals are therefore **not active**. The current account `mcgrath-bpt` is the only collaborator and cannot approve its own PRs. [CODEOWNERS](../.github/CODEOWNERS) names the platform owner; this is routing, not enforcement. CI gates cannot prove Tech Lead approval and a policy-changing PR could still be merged by its author. Do not mark DC-032 complete on this basis.

After the second account has write permission, add both authorised reviewers to CODEOWNERS on the default branch, check the scope, then run:

```sh
python3 scripts/repository_rules.py --apply --activate-review
```

[The additional review rules](../governance/github-review.json) require one code-owner approval, dismiss stale approvals and require approval of the latest reviewable push, with no bypass actors. A repository administrator can still change policy through settings; review controls protect ordinary merges, not against an administrator deliberately removing controls. GitHub documents [code ownership](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners) and [rulesets](https://docs.github.com/en/rest/repos/rules).

Activation acceptance must use a disposable PR: show an unapproved baseline/dependency change blocked, a changed commit invalidating approval, a missing/failed required check blocking merge, and the approved/current checks allowing merge. Inspect the remote rule evaluation and PR state; local JSON/tests alone do not prove enforcement. Repeat the applicable ownership/review controls in Opharma before claiming delivery dependency enforcement. Do not make unauthorised business-code changes there.
