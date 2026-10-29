# Repository instructions

- Use British English in responses and team-facing documentation.
- Avoid the word "agnostic"; prefer "indifferent".
- "Test yourself, before you wreck yourself." Run checks appropriate to the change and report observed results and limitations.
- Use dates in `YYYY-MM-dd` format. Add `HH:mm:ss` and a timezone or UTC offset where needed; machine timestamps use ISO 8601 with an explicit offset or `Z`.
- Read [CONTRIBUTING.md](CONTRIBUTING.md), [the operating model](docs/OPERATING_MODEL.md) and the relevant backlog item before implementation.
- On resuming this work, read [HANDOVER.md](HANDOVER.md) and recheck Git/Docker access before assuming previous session restrictions still apply.
- Prefer the latest stable Python for the workspace, pinned to an exact version. The current target is 3.15.2; host tooling requires stable Python 3.12 or later. Record compatibility evidence before claiming a qualified release.
- Keep Datacon platform changes here and pipeline business logic in its independent delivery repository.
- Delivery dependency changes require Tech Lead agreement and reproducible provision through this platform repository.
- Preserve retained checkouts and uncommitted work. Reset operations must be explicit and scoped.
- Never commit credentials or runtime databases. Record real validation evidence; generated files and static checks do not establish native runtime success.
