# Independent delivery workspaces

Updated: 2026-10-30. The `project` commands attach independent repositories to one Datacon instance and give each a database, login role and persistent credential. They use the existing approved core dependencies. See [observed acceptance](evidence/2026-10-30-delivery-workspaces.md) for native runs and graphical editor evidence.

## Register existing checkouts

Run host commands from Datacon. Choose an instance name; `init` creates its local state without starting services. A host binding requires an existing Git checkout root. Paths with spaces and dollar signs are supported; quote them in your shell.

```sh
./datacon --instance delivery init
./datacon --instance delivery project add sample --host-path '/absolute/path/to/sample'
./datacon --instance delivery up
```

The checkout appears at `/projects/sample`. Host writes and container writes affect the same files. Datacon refuses missing paths, nested directories mistaken for repository roots and working directories escaping the checkout. It never copies a checkout into the platform source tree or alters its Git configuration.

Alternatively, clone inside the persistent workspace. For the existing Opharma layout:

```sh
./datacon --instance delivery exec -- git clone https://github.com/mcgrath-bpt/opharma.git /workspaces/opharma
./datacon --instance delivery project add opharma --container-path /workspaces/opharma --workdir pharma-commercial-lab
./datacon --instance delivery up
./datacon --instance delivery project list
```

Use your delivery's approved revision or feature branch before making changes. The acceptance harness selects the exact revision in `platform/reference.json`; ordinary registration preserves your current branch and dirty files. Project names contain 1–32 lower-case letters, digits or hyphens and start with a letter. Repeating an identical registration is safe; changing an existing binding is refused.

After adding a project, `up` attaches its mounts and credential. This may recreate the shared workspace container and interrupt other terminals in that instance. `up` and `down` remain instance-wide operations; repositories, home state and database volumes persist.

## Run with a project's database identity

```sh
./datacon --instance delivery project provision sample
./datacon --instance delivery project provision opharma
./datacon --instance delivery project exec opharma -- python -m unittest discover -s tests -v
./datacon --instance delivery project exec sample -- psql -c 'SELECT current_database(), current_user;'
./datacon --instance delivery project shell opharma
```

`exec` and `shell` select the registered working directory and `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER` and `PGPASSWORD`. Passwords are read inside the container; they are absent from command arguments and generated descriptors. The wrapper removes inherited PostgreSQL service/options/password-file settings and `DATABASE_URL`. Configure other application-specific connection settings explicitly if your application uses them instead of PostgreSQL's standard variables.

Each project uses database/role `dc_<name>`, an owned `workspace` schema and pg_duckdb access. The login cannot create roles/databases, become another project's role or connect to another project's database. PostgreSQL owns the database itself. Reprovisioning preserves its contents and credential. Ownership markers tie provision/reset operations to this local registry; unmanaged databases, unmanaged roles and unexpectedly privileged roles are refused.

These identities prevent accidental cross-project SQL access under the selected role. This is one trusted developer's shared workspace: all registered credentials and checkouts are available to that developer. It is not a hostile multi-user security boundary. Use separate instances or stronger isolation for separate trust domains. The original instance-level `developer` role and existing CLI commands remain available.

## Open the delivery in VS Code

```sh
./datacon --instance delivery project editor opharma
```

The command prints an ignored local folder under `.local/instances/delivery/editors/opharma`. Open that folder in VS Code, then run **Dev Containers: Reopen in Container**. Review/trust your generated configuration when prompted. It opens the delivery's working directory as non-root `developer`, uses the same named instance and leaves services running when the window closes.

New integrated terminals use the **Datacon project** profile, which selects the project's directory and database identity. Python's default interpreter is `/opt/datacon/venv/bin/python`. Tasks and extensions that do not use this terminal profile should invoke the project wrapper or supply their own approved connection configuration; they do not automatically inherit its process environment. No editor descriptor is written into the delivery repository.

New Linux instances record the host's unprivileged UID/GID so host-mounted files remain writable. macOS and existing instances retain UID/GID 1000. The IDs are persisted in `workspace.json`; do not change them underneath retained volumes. Existing Linux instances created with UID 1000 require compatible host permissions or a separately named new instance; Datacon does not recursively change ownership of retained files.

## Reset only one project's database

```sh
./datacon --instance delivery project reset-db opharma --confirm opharma
```

This explicitly drops and recreates **all data in `dc_opharma`**, terminating connections to that database. It preserves the checkout, credential, role and other projects' databases. The exact project-name confirmation and registry ownership markers are mandatory. It cannot reset an unprovisioned or unmanaged database. Normal `project provision` is non-destructive.

Keep `.local/instances/<instance>/` with the matching Docker volumes. It contains credentials, registry ownership IDs, persisted UID/GID and generated Compose/editor files; none belongs in Git. Lost credentials/registry must be restored from a trusted backup, not regenerated to adopt retained databases. A provision interrupted before its ownership marker is recorded fails conservatively on retry and needs inspection/recovery by the instance owner. No automatic adoption, unregister, checkout deletion or volume prune operation is provided.

## Repeat acceptance

```sh
python3 scripts/qualify_projects.py --expected-architecture arm64
# Native Linux AMD64 host:
python3 scripts/qualify_projects.py --expected-architecture amd64
```

The shared script creates a uniquely named instance, an independent host Git fixture and a pinned Opharma clone. It tests both repositories, both SQL identities, denied cross-project operations, bidirectional mounting, idempotent provisioning, scoped reset and recreation with dirty files/credentials preserved. Its evidence includes input hashes, versions and image identities. The tiny host repository is generated acceptance data outside exported evidence, not delivery business logic in Datacon.

By default it removes only its own containers/network and retains volumes, credentials and source checkouts. `--keep-running` keeps a successful instance for a separate graphical check. Automated evidence explicitly records graphical attachment as `NOT_EXECUTED`; the real VS Code exercise is recorded separately. CI runs this script after the existing two-build core qualification and uploads sanitised reports on success or failure. Actual Windows/WSL, clean-machine onboarding, additional dependency environments and immutable releases remain separate acceptance work.
