"""Host-owned delivery registry, Compose mounts and scoped database lifecycle."""

from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import subprocess
import uuid

NAME = re.compile(r'[a-z][a-z0-9-]{0,31}\Z')


class ProjectError(Exception):
    pass


def project_name(value):
    if not NAME.fullmatch(value):
        raise ProjectError('Project names require 1–32 lower-case letters, digits or hyphens, starting with a letter.')
    return value


def workdir(value):
    path = PurePosixPath(value)
    if path.is_absolute() or '..' in path.parts or any(c in value for c in '\n\r\x00'):
        raise ProjectError('Working directory must stay inside the repository.')
    return str(path)


def read_registry(state):
    path = state / 'projects.json'
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
        if data['version'] != 1 or not isinstance(data['projects'], dict):
            raise ValueError()
        for name, entry in data['projects'].items():
            project_name(name)
            workdir(entry['workdir'])
            if str(uuid.UUID(entry['id'])) != entry['id'] or entry['name'] != name:
                raise ValueError()
            if entry['kind'] not in ('host', 'volume'):
                raise ValueError()
        return data['projects']
    except (ValueError, KeyError, TypeError) as error:
        raise ProjectError('Invalid project registry; restore it rather than adopting existing databases.') from error


def save_json(path, data):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, indent=2) + '\n')
    temporary.replace(path)


@contextmanager
def locked(state):
    with (state / 'projects.lock').open('a') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ProjectError('Another project operation is running for this instance.') from error
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def compose_overlay(state, entries):
    # Compose interpolates dollar signs even in JSON string values.
    escaped = lambda path: str(path).replace('$', '$$')
    workspace = {'volumes': [], 'secrets': []}
    overlay = {'services': {'workspace': workspace, 'toolchain': workspace}, 'secrets': {}}
    for name, entry in sorted(entries.items()):
        if entry['kind'] == 'host':
            workspace['volumes'].append({'type': 'bind', 'source': escaped(entry['source']),
                'target': entry['container_path'], 'bind': {'create_host_path': False}})
        key = 'project_' + name
        workspace['secrets'].append({'source': key, 'target': key})
        overlay['secrets'][key] = {'file': escaped(state / 'projects' / name / 'password')}
    save_json(state / 'projects.compose.json', overlay)


def check_host_checkout(path, directory):
    path = Path(path).expanduser().resolve(strict=True)
    if any(c in str(path) for c in '\n\r\x00'):
        raise ProjectError('Checkout paths cannot contain control characters.')
    result = subprocess.run(['git', '-C', str(path), 'rev-parse', '--show-toplevel'],
                            text=True, capture_output=True)
    if result.returncode or Path(result.stdout.strip()).resolve() != path:
        raise ProjectError('Host path must name the root of an existing independent Git checkout.')
    selected = (path / directory).resolve(strict=True)
    if not selected.is_relative_to(path) or not selected.is_dir():
        raise ProjectError('Working directory must resolve inside the checkout.')
    return str(path)


def identity(entry):
    name = project_name(entry['name'])
    return 'dc_' + name, 'datacon-project:' + str(uuid.UUID(entry['id']))


def sql_literal(value):
    return "'" + value.replace("'", "''") + "'"


def sql_identifier(value):
    return '"' + value.replace('"', '""') + '"'


class Manager:
    def __init__(self, instance, root, compose, env):
        self.instance, self.root, self.compose, self.env = instance, root, compose, env
        self.state = root / '.local/instances' / instance
        if not self.state.is_dir():
            raise ProjectError('Initialise this instance with datacon --instance <name> init first.')

    def command(self, *arguments):
        return self.compose(self.instance, *arguments, root=self.root)

    def run(self, arguments, *, input=None, timeout=60):
        result = subprocess.run(self.command(*arguments), env=self.env, input=input,
                                text=True, capture_output=True, timeout=timeout)
        if result.returncode:
            # Never include SQL/password input or Docker diagnostics in errors.
            raise ProjectError('Project command failed. Check instance readiness and the selected checkout; credentials were not printed.')
        return result.stdout

    def entry(self, name):
        name = project_name(name)
        entries = read_registry(self.state)
        if name not in entries:
            raise ProjectError('Project is not registered in this instance: ' + name)
        entry = entries[name]
        password = self.state / 'projects' / name / 'password'
        if not password.is_file() or not re.fullmatch(r'[A-Za-z0-9_-]{40,}', password.read_text().strip()):
            raise ProjectError('Project credentials are missing or invalid; restore them, do not rotate retained credentials.')
        return entry

    def add(self, name, host_path, container_path, directory):
        name, directory = project_name(name), workdir(directory)
        if host_path:
            source = check_host_checkout(host_path, directory)
            kind, target = 'host', '/projects/' + name
        else:
            path = PurePosixPath(container_path)
            if not path.is_absolute() or '..' in path.parts or not str(path).startswith('/workspaces/'):
                raise ProjectError('Volume checkouts must be rooted below /workspaces/.')
            code = """import json, subprocess, sys
from pathlib import Path
p=Path(sys.argv[1]).resolve(strict=True)
w=(p/sys.argv[2]).resolve(strict=True)
assert p.is_relative_to('/workspaces') and p != Path('/workspaces')
assert w.is_relative_to(p) and w.is_dir()
assert Path(subprocess.check_output(['git','-C',str(p),'rev-parse','--show-toplevel'],text=True).strip()).resolve()==p
print(json.dumps(str(p)))
"""
            source = json.loads(self.run(['exec', '-T', 'workspace', 'python', '-c', code, str(path), directory]))
            kind, target = 'volume', source
        entries = read_registry(self.state)
        candidate = {'name': name, 'kind': kind, 'source': source, 'container_path': target, 'workdir': directory}
        if name in entries:
            existing = self.entry(name)
            if any(existing[key] != value for key, value in candidate.items()):
                raise ProjectError('Project already has a different binding; retained state has not been changed.')
            compose_overlay(self.state, entries)
            return existing
        if any(e['source'] == source and e['kind'] == kind for e in entries.values()):
            raise ProjectError('That checkout is already registered under another project name.')
        folder = self.state / 'projects' / name
        folder.mkdir(parents=True, mode=0o700, exist_ok=False)
        with (folder / 'password').open('x') as stream:
            os.chmod(folder / 'password', 0o444)
            stream.write(secrets.token_urlsafe(32) + '\n')
        candidate['id'] = str(uuid.uuid4())
        entries[name] = candidate
        save_json(self.state / 'projects.json', {'version': 1, 'projects': entries})
        compose_overlay(self.state, entries)
        return candidate

    def sql(self, query, database='postgres'):
        return self.run(['exec', '-T', 'warehouse', 'psql', '-U', 'postgres', '-d', database,
                         '-X', '-qAt', '--set', 'ON_ERROR_STOP=1'], input=query)

    def inspect_database(self, entry):
        identifier, marker = identity(entry)
        value = sql_literal(identifier)
        query = f"""SELECT json_build_object(
'role', (SELECT json_build_object('marker', shobj_description(oid, 'pg_authid'),
    'safe', NOT (rolsuper OR rolcreatedb OR rolcreaterole OR rolbypassrls OR rolreplication)) FROM pg_roles WHERE rolname={value}),
'database', (SELECT json_build_object('marker', shobj_description(oid, 'pg_database'),
    'owner', pg_get_userbyid(datdba)) FROM pg_database WHERE datname={value}));
"""
        status = json.loads(self.sql(query))
        role, database = status['role'], status['database']
        if role and (role['marker'] != marker or not role['safe']):
            raise ProjectError('Refusing to modify an unmanaged or unexpectedly privileged project role.')
        if database and (database['marker'] != marker or database['owner'] != 'postgres'):
            raise ProjectError('Refusing to modify an unmanaged project database.')
        if database and not role:
            raise ProjectError('Project role is missing for retained database; restore its state before proceeding.')
        return status

    def provision(self, name, reset=False, confirmation=None):
        entry = self.entry(name)
        if reset and confirmation != name:
            raise ProjectError('Database reset requires --confirm followed by the exact project name.')
        status = self.inspect_database(entry)
        identifier, marker = identity(entry)
        quoted = sql_identifier(identifier)
        if reset:
            if not status['database'] or not status['role']:
                raise ProjectError('Cannot reset a project that has not been provisioned.')
            # Only this managed database is touched; no checkout or other database is reset.
            self.sql(f'DROP DATABASE {quoted} WITH (FORCE);')
            status['database'] = None
        if not status['role']:
            password = (self.state / 'projects' / name / 'password').read_text().strip()
            self.sql(f"""BEGIN;
CREATE ROLE {quoted} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS NOREPLICATION CONNECTION LIMIT 3 PASSWORD {sql_literal(password)};
COMMENT ON ROLE {quoted} IS {sql_literal(marker)};
GRANT datacon_duckdb TO {quoted};
COMMIT;
""")
        if not status['database']:
            self.sql(f'CREATE DATABASE {quoted} OWNER postgres TEMPLATE template0 CONNECTION LIMIT 3 ALLOW_CONNECTIONS false;\n'
                     f'COMMENT ON DATABASE {quoted} IS {sql_literal(marker)};')
        self.sql(f'BEGIN; REVOKE ALL ON DATABASE {quoted} FROM PUBLIC; '
                 f'GRANT CONNECT, TEMPORARY ON DATABASE {quoted} TO {quoted}; '
                 f'ALTER DATABASE {quoted} ALLOW_CONNECTIONS true; COMMIT;')
        # Reapplying grants is safe and repairs an interrupted initial provision.
        self.sql(f"""BEGIN;
REVOKE ALL ON DATABASE {quoted} FROM PUBLIC;
GRANT CONNECT, TEMPORARY ON DATABASE {quoted} TO {quoted};
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO {quoted};
CREATE EXTENSION IF NOT EXISTS pg_duckdb;
CREATE SCHEMA IF NOT EXISTS workspace AUTHORIZATION {quoted};
ALTER ROLE {quoted} IN DATABASE {quoted} SET search_path = workspace, public;
COMMIT;
""", database=identifier)
        return identifier

    def execute(self, name, command):
        entry = self.entry(name)
        if not command:
            raise ProjectError('Provide a command after --.')
        identifier, _ = identity(entry)
        flags = [] if os.isatty(0) else ['-T']
        arguments = ['exec', *flags, 'workspace', 'python', '/opt/datacon/scripts/project_exec.py',
                     '--database', identifier, '--password-file', '/run/secrets/project_' + name,
                     '--repository', entry['container_path'], '--workdir', entry['workdir'], '--', *command]
        return subprocess.run(self.command(*arguments), env=self.env).returncode

    def editor(self, name):
        entry = self.entry(name)
        # Generated configuration stays in the ignored local registry, outside delivery Git history.
        folder = self.state / 'editors' / name
        descriptor = folder / '.devcontainer/devcontainer.json'
        descriptor.parent.mkdir(parents=True, exist_ok=True)
        database, _ = identity(entry)
        terminal_args = ['/opt/datacon/scripts/project_exec.py', '--database', database,
            '--password-file', '/run/secrets/project_' + name, '--repository', entry['container_path'],
            '--workdir', entry['workdir'], '--', '/bin/bash']
        save_json(descriptor, {'name': 'Datacon: ' + name + ' (' + self.instance + ')',
            'dockerComposeFile': [str(self.root / 'compose.yaml'), str(self.state / 'instance.compose.json'), str(self.state / 'projects.compose.json')],
            'service': 'workspace', 'runServices': ['workspace', 'warehouse'],
            'workspaceFolder': str(PurePosixPath(entry['container_path']) / entry['workdir']),
            'remoteUser': 'developer', 'updateRemoteUserUID': False, 'overrideCommand': False,
            'shutdownAction': 'none', 'initializeCommand': [str(self.root / 'datacon'), '--instance', self.instance, 'init'],
            'customizations': {'vscode': {'settings': {
                'python.defaultInterpreterPath': '/opt/datacon/venv/bin/python',
                'terminal.integrated.profiles.linux': {'Datacon project': {'path': '/opt/datacon/venv/bin/python', 'args': terminal_args}},
                'terminal.integrated.defaultProfile.linux': 'Datacon project',
            }}}})
        return folder


def handle(args, instance, root, compose, env):
    manager = Manager(instance, root, compose, env)
    if args.project_action == 'list':
        print(json.dumps(read_registry(manager.state), indent=2))
        return 0
    if args.project_action in ('exec', 'shell'):
        command = ['bash'] if args.project_action == 'shell' else args.command
        if command[:1] == ['--']:
            command = command[1:]
        return manager.execute(args.name, command)
    with locked(manager.state):
        if args.project_action == 'add':
            manager.add(args.name, args.host_path, args.container_path, args.workdir)
            print('Registered ' + args.name + '. Run up to attach mounts/credentials, then project provision ' + args.name + '.')
        elif args.project_action in ('provision', 'reset-db'):
            database = manager.provision(args.name, reset=args.project_action == 'reset-db', confirmation=getattr(args, 'confirm', None))
            print('Project database ready: ' + database + '. Checkout and other projects preserved.')
        elif args.project_action == 'editor':
            print(manager.editor(args.name))
    return 0


def add_parser(commands):
    parser = commands.add_parser('project', help='Register checkouts and manage isolated delivery databases')
    actions = parser.add_subparsers(dest='project_action', required=True)
    add = actions.add_parser('add', help='Register an existing checkout without changing its files')
    add.add_argument('name')
    sources = add.add_mutually_exclusive_group(required=True)
    sources.add_argument('--host-path')
    sources.add_argument('--container-path')
    add.add_argument('--workdir', default='.')
    actions.add_parser('list', help='Show local bindings, without credentials')
    for command in ('provision', 'reset-db', 'editor', 'shell', 'exec'):
        action = actions.add_parser(command)
        action.add_argument('name')
        if command == 'reset-db':
            action.add_argument('--confirm', required=True, help='Repeat the exact project name; drops only its managed database')
        if command == 'exec':
            action.add_argument('command', nargs='...')
