# Initial core implementation evidence

Historical record: the later [core runtime acceptance](2026-10-29-core-runtime.md) supersedes the access blockers and unexecuted core checks below. These earlier observations are retained as recorded.

Recorded: 2026-10-29. Baseline commit: `601cee36cf6e9c6970620bca34ea0046eb6ea90c`. The core candidate is an uncommitted working-tree change on that baseline; it has no release identity yet.

## Observed environment

| Item | Observation |
| --- | --- |
| Host | macOS, ARM64 |
| Host Python for tests/launcher | 3.9.6 |
| Docker CLI | 29.9.2 |
| Docker Compose | 5.6.1 |
| Git | 2.56.0 |
| Initial repository | Clean `main` at `601cee3`; no remote |

## Completed checks

| Check | Observed result |
| --- | --- |
| `./datacon check` | 15 tests passed: credential retention, instance separation, invalid names, fresh-state refusal, retained/unlabelled Docker resource guards, shutdown volume preservation, literal command arguments, failure propagation, diagnostic redaction and replay multiset comparison |
| `./datacon config` | Passed using the installed Compose parser without a daemon |
| `./datacon --instance example-task config` | Passed for a named instance |
| Rendered Compose inspection | Confirmed two core services, non-root workspace, developer-only workspace credential, no host ports, instance-scoped volumes and warehouse memory cap |
| Python/JSON/shell syntax | Passed source parsing and `sh -n` for the launcher/database initialisation script |
| Documentation/source checks | Local Markdown links, code fences, LF/final newline, whitespace and 34 stable backlog IDs passed |
| `git diff --check` | Passed for tracked changes; the source audit also covered new files |
| `./datacon doctor --json` | Correctly returned exit status 1 with `daemon_available: false` and `runtime_qualification: NOT_EXECUTED` |

These are host-side tests and configuration checks. They do not establish container startup, RLS correctness, persistence through actual Docker recreation or Opharma acceptance.

## Unexecuted checks and observed blockers

- Docker initially had no socket. A later `docker info` attempt returned permission denied for `/Users/mmcgrath/.docker/run/docker.sock`. This session could not access the daemon, so no image build, container startup, database smoke, reference run or resource measurement was performed.
- Shell `git ls-remote` could not resolve `github.com`. Connected GitHub read tools supplied upstream source inspection, but no independent delivery checkout was created by this session.
- Creating branch `feat/DC-002-core-runtime` failed while writing `.git/refs/heads/...`. No new branch, staged files or implementation commit was created.
- No Windows/WSL host, Linux AMD64 container build, editor attachment, Snowflake account or catalogue integration was exercised.

## Next acceptance run

From a terminal with Docker access, follow [the core quick-start](../CORE_QUICKSTART.md): run doctor, build/start, smoke and reference. Record actual image IDs/digests and installed versions. Exercise `down`/`up` with an uncommitted project file and verify a separate `fresh` instance leaves it intact. Add the resulting evidence and resolve failures before marking any runtime backlog item done or publishing an approved release.

## Handover update — 2026-10-29

The user requested the latest stable Python with a 3.12 minimum and a next-session handover. The image target was changed to `python:3.15.2-slim-bookworm`, verified in Python's release list and the official Docker image manifest. `.python-version` records the same target. `rpds-py` was changed to 2026.9.1 after verifying published CPython 3.15 Linux ARM64/AMD64 wheels. These are source/registry checks, not executed install tests.

The host launcher now selects an installed stable Python >=3.12, supports an explicit executable override and is also used by Dev Container initialisation. It selects Python 3.14.8 on this Mac. Docker diagnostics now distinguish `access_denied` from an unreachable daemon and suppress raw potentially sensitive errors.

| Check | Updated observation |
| --- | --- |
| `./datacon check` | 23 tests passed on Python 3.14.8, including interpreter selection/rejection/override and denied Docker access diagnostics |
| `DATACON_PYTHON=/opt/homebrew/bin/python3.12 ./datacon check` | 23 tests passed on Python 3.12.15, exercising the minimum supported minor version |
| `./datacon config` and shell syntax | Passed after the Python/launcher changes |
| `./datacon doctor --json` | Python 3.14.8, target 3.15.2, `docker_error: access_denied`; expected exit 1 |
| Direct Docker socket probe | Socket exists; connection returned `errno=1`, `Operation not permitted` |
| Git branch creation retry | Still rejected when creating the branch ref; `.git` owner/mode normal and managed session policy read-only |

The current session disables sandbox approval requests; no escalation was submitted or granted. This is an enforced sandbox denial, not a reported automatic-review decision. Global Codex configuration inspection did not identify an explicit matching permission setting, and no user/system permission configuration was changed.

All container/native checks listed above remain unexecuted. [HANDOVER.md](../../HANDOVER.md) records the complete state, next steps and commit preparation. Initial results above are retained as history rather than rewritten as newer Python evidence.
