# Core dependency locks and qualification

Recorded: 2026-10-29. This covers the existing Python/JSON Schema workspace and PostgreSQL/pg_duckdb core. GX, Snowflake adapters, catalogue dependencies, WSL, graphical editor acceptance, resource certification and release publication remain separate gates. DC-007 remains open.

## Locked inputs

The Python 3.15.2 and pg_duckdb image tags retain their approved multi-platform SHA-256 digests in the Dockerfile and Compose file. The warehouse receives no package installation; its complete package inventory and image identity are recorded during qualification.

`requirements/workspace.txt` retains the six existing versions, with SHA-256 hashes for five universal wheels and the two CPython 3.15 Linux ARM64/AMD64 rpds wheels. [The wheel provenance](../requirements/workspace-wheels.json) records their published filenames, URLs and hashes. Installation requires `--only-binary=:all:` and `--require-hashes`, then `pip check`, following [pip's supported secure-install options](https://pip.pypa.io/en/stable/topics/secure-installs/). The bootstrap pip comes from the digest-pinned Python image and is included in the installed inventory.

The workspace uses these [Debian snapshot archives](https://snapshot.debian.org/):

| Archive | Requested UTC timestamp | Suites |
| --- | --- | --- |
| debian | `20261027T000000Z` (2026-10-27 00:00:00 UTC) | bookworm, bookworm-updates |
| debian-security | `20261027T000000Z` (2026-10-27 00:00:00 UTC) | bookworm-security |

Snapshot resolves each timestamp to the latest import at or before it. `requirements/os/debian.sources` replaces the base image's floating source file. HTTPS, Debian archive keys and signed Release/package hash verification remain enabled. Only the Release expiry check is disabled (`Check-Valid-Until: no`), as required for a historical archive; neither trusted sources nor unauthenticated installation are enabled.

The [ARM64 inventory](../requirements/os/bookworm-arm64.tsv) and [AMD64 inventory](../requirements/os/bookworm-amd64.tsv) each list every installed Debian package, exact version (including epoch/revision) and architecture, including inherited base packages. The `os-locked` build stage compares the complete inventory and fails with a diff on any addition, removal or version change. It has no skip flag. The `os-candidate` intermediate target exists solely to produce review candidates.

## Run the same acceptance locally and in CI

From the repository root, with stable host Python 3.12 or later and Docker/Compose available:

```sh
python3.12 scripts/qualify.py
```

Use an installed supported interpreter (for example `python3.14` on the current Mac). The script generates a unique `qual-...` instance, refuses existing evidence directories, performs two `--pull --no-cache` builds and starts services through the existing `datacon` commands. Both runs collect Python/OS inventories and image identities, check non-root/database/RLS/DuckDB smoke and both restart policies, and execute the pinned reference (35 tests, one expected skip, 14 initial and replay checkpoints, identical table row multisets). It compares installed dependencies, not image IDs. It also requires an incorrect wheel hash and an altered OS lock to fail for their specific integrity errors.

The host, daemon and image architectures must agree. Emulated builds can prepare an inventory but cannot pass native qualification. [GitHub's runner reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners) identifies `ubuntu-24.04` as x64. The workflow runs on pull requests, pushes to `main` and manual dispatch, with read-only repository permissions, SHA-pinned actions, no persisted checkout credentials and a 30-minute job timeout (18 minutes for core qualification and eight for the two-project workflow, reserving upload time). Manual dispatch becomes available after the workflow reaches the default branch.

Evidence defaults to `.local/qualification/<instance>/`. CI uses `artifacts/core-qualification/` and uploads it even on failure, retaining the artefact for 30 days. Only command transcripts, selected identity fields, package inventories and the four named reference JSON reports are collected. Instance secret values and authenticated URLs are redacted; full Docker inspect/environment output, credentials, databases, fixture directories and checkouts are never copied. Review evidence before committing it. A run failing before Docker starts still leaves a failure summary. A forced runner termination may interrupt cleanup; GitHub discards its VM.

Normal completion or failure removes only that qualification instance's containers using `datacon --instance <name> down`. All named volumes and local credentials remain. No prune or volume deletion is performed. Existing instances and dirty delivery checkouts remain untouched. The script does not change the existing CLI or certify branch protection.

## Deliberate refresh procedure

1. Agree dependency/version or security updates with the Tech Lead and create a focused branch. Snapshot locks freeze security updates too: review them deliberately, never silently follow a mirror.
2. Keep or deliberately update each base digest and the Python target. Select and record the two archive timestamps in `debian.sources` and this document. Review upstream advisories and compatibility before advancing them.
3. Build only the candidate stage for each architecture. Use a native host where available; clearly label any emulated generation. For example:

   ```sh
   docker build --pull --no-cache --platform linux/arm64 --target os-candidate -f .devcontainer/Dockerfile -t datacon-os-candidate:arm64 .
   docker run --rm --platform linux/arm64 -v "$PWD/scripts/verify_os.py:/tmp/verify_os.py:ro" datacon-os-candidate:arm64 python /tmp/verify_os.py --inventory > .local/bookworm-arm64.candidate.tsv
   ```

   Repeat with `amd64`. Inspect complete diffs against the committed inventories; only copy reviewed candidates into `requirements/os/bookworm-<architecture>.tsv`. Do not remove the verification stage to make a build pass.
4. For any wheel change, query the exact release's PyPI JSON metadata, select only the supported wheel filenames, download them, and calculate SHA-256 independently. Compare it with the published digest; update both the requirements hashes and provenance JSON. Keep every transitive requirement pinned. Do not add source distributions or unapproved wheels as a workaround.
5. Run the shared qualification on native ARM64 and native AMD64, including both uncached builds and deliberate failure checks. Record actual run URLs, revisions, versions and sanitised evidence. Review inventory differences and compatibility; retain all prior qualification instances until explicitly authorised for removal.
6. Update the handover/backlog and obtain normal PR review. Lock refresh does not publish a release or satisfy the wider DC-007 capability gates.
