#!/usr/bin/env python3
"""Native two-repository acceptance in a new instance; never resets retained work."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import uuid

import datacon
from qualify import Qualification, assert_native

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--expected-architecture', choices=('arm64', 'amd64'))
    parser.add_argument('--keep-running', action='store_true', help='Retain this new instance for graphical acceptance')
    args = parser.parse_args()
    instance = 'projects-' + datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S') + '-' + uuid.uuid4().hex[:6]
    output = (args.output or ROOT / '.local/project-qualification' / instance).resolve()
    output.mkdir(parents=True, exist_ok=False)
    runner = Qualification(output, instance)
    runner.summary['scope'] = 'DC-002/DC-003 two independent repositories, mounts, identities and scoped reset'
    owned = False
    try:
        runner.save('qualification.json', runner.summary)
        runner.summary['platform_commit'] = runner.run('revision', ['git', 'rev-parse', 'HEAD']).strip()
        runner.summary['input_sha256'] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for pattern in ('scripts/*.py', 'compose.yaml', '.devcontainer/Dockerfile') for p in sorted(ROOT.glob(pattern))}
        doctor = json.loads(runner.cli('doctor', 'doctor', '--json'))
        architecture = assert_native(platform.machine(), doctor['daemon_architecture'], args.expected_architecture)
        runner.summary.update(native=True, architecture=architecture)
        runner.cli('host-tests', 'check')
        runner.cli('initialise', 'init')
        owned = True
        state = datacon.state_path(instance)
        # This independent, deliberately tiny Git repository is acceptance data only.
        # Its source tree lives outside the exported evidence directory.
        host = ROOT / '.local/project-qualification' / (instance + '-sources') / 'Sample delivery $ path'
        host.mkdir(parents=True, exist_ok=False)
        (host / 'test_delivery.py').write_text("import unittest\nfrom pathlib import Path\nimport jsonschema\nclass DeliveryTest(unittest.TestCase):\n    def test_workspace(self):\n        self.assertTrue(Path('README.md').is_file())\n        jsonschema.validate({'value':7},{'type':'object'})\n")
        (host / 'README.md').write_text('# Independent acceptance delivery\n')
        runner.run('sample-git-init', ['git', 'init', '-q', str(host)])
        runner.run('sample-git-add', ['git', '-C', str(host), 'add', 'README.md', 'test_delivery.py'])
        runner.run('sample-git-commit', ['git', '-C', str(host), '-c', 'user.name=Datacon acceptance', '-c',
                                       'user.email=acceptance@example.invalid', 'commit', '-qm', 'Independent acceptance fixture'])
        (host / 'unfinished.txt').write_text('Retain this uncommitted sample work.\n')
        runner.cli('register-host', 'project', 'add', 'sample', '--host-path', str(host))
        runner.secrets = [p.read_text().strip() for p in state.glob('*_password')] + [p.read_text().strip() for p in state.glob('projects/*/password')]
        runner.cli('start', 'up', timeout=720)
        spec = json.loads((ROOT / 'platform/reference.json').read_text())
        runner.cli('clone-opharma', 'exec', '--', 'git', 'clone', '--no-checkout', '--filter=blob:none', spec['repository'], '/workspaces/opharma', timeout=180)
        runner.cli('checkout-opharma', 'exec', '--', 'git', '-C', '/workspaces/opharma', 'checkout', '--detach', spec['commit'])
        runner.cli('register-volume', 'project', 'add', 'opharma', '--container-path', '/workspaces/opharma', '--workdir', spec['subdirectory'])
        runner.secrets += [(state / 'projects/opharma/password').read_text().strip()]
        credentials_before = {p.relative_to(state).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in [*state.glob('*_password'), *state.glob('projects/*/password')]}
        runner.cli('attach-project-secrets', 'up', timeout=240)
        for name in ('opharma', 'sample'):
            runner.cli('provision-' + name, 'project', 'provision', name)
        def execute(label, name, *command, **kwargs):
            return runner.cli(label, 'project', 'exec', name, '--', *command, **kwargs)
        def sql(label, name, query, **kwargs):
            return execute(label, name, 'psql', '-X', '-qAt', '--set', 'ON_ERROR_STOP=1', '-c', query, **kwargs)
        for name in ('opharma', 'sample'):
            sql('seed-' + name, name, "CREATE TABLE workspace.probe(value integer); INSERT INTO workspace.probe VALUES (7);")
            assert sql('role-' + name, name, 'SELECT current_user;').strip() == 'dc_' + name
            execute('smoke-' + name, name, 'python', '/opt/datacon/scripts/smoke.py')
        for name, other in (('opharma', 'sample'), ('sample', 'opharma')):
            execute('deny-connect-' + name, name, 'psql', '-X', '-d', 'dc_' + other, '-c', 'SELECT 1', expected_failure='permission denied for database')
            sql('deny-set-role-' + name, name, 'SET ROLE "dc_' + other + '";', expected_failure='permission denied')
            sql('deny-drop-' + name, name, 'DROP DATABASE "dc_' + other + '";', expected_failure='must be owner')
        sql('deny-role-creation', 'sample', 'CREATE ROLE should_not_exist;', expected_failure='permission denied')
        runner.cli('reject-wrong-reset', 'project', 'reset-db', 'opharma', '--confirm', 'sample', expected_failure='exact project name')
        execute('sample-tests', 'sample', 'python', '-m', 'unittest', '-v')
        execute('opharma-tests', 'opharma', 'python', '-m', 'unittest', 'discover', '-s', 'tests', '-v', timeout=180)
        execute('opharma-contracts', 'opharma', 'python', 'src/odcs.py')
        execute('dirty-opharma', 'opharma', 'python', '-c', "from pathlib import Path; Path('../unfinished.txt').write_text('Retain Opharma work.\\n')")
        execute('write-through-bind', 'sample', 'python', '-c', "from pathlib import Path; Path('from-container.txt').write_text('container write\\n')")
        assert (host / 'from-container.txt').read_text() == 'container write\n'
        (host / 'from-host.txt').write_text('host write\n')
        execute('read-through-bind', 'sample', 'python', '-c', "from pathlib import Path; assert Path('from-host.txt').read_text()=='host write\\n'")
        snapshot_code = """import hashlib,json,subprocess
from pathlib import Path
root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip())
print(json.dumps({'revision':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
'status':subprocess.check_output(['git','status','--porcelain'],text=True),
'probe_sha256':hashlib.sha256((root/'unfinished.txt').read_bytes()).hexdigest()}))
"""
        before = {name: json.loads(execute('before-' + name, name, 'python', '-c', snapshot_code)) for name in ('opharma', 'sample')}
        assert before['opharma']['revision'] == spec['commit']
        assert before['opharma']['revision'] != before['sample']['revision']
        for name in ('opharma', 'sample'):
            runner.cli('reprovision-' + name, 'project', 'provision', name)
            assert sql('reprovision-preserves-' + name, name, 'SELECT value FROM workspace.probe;').strip() == '7'
        runner.cli('reset-opharma-only', 'project', 'reset-db', 'opharma', '--confirm', 'opharma')
        assert sql('reset-cleared-opharma', 'opharma', "SELECT to_regclass('workspace.probe') IS NULL;").strip() == 't'
        assert sql('reset-preserved-sample', 'sample', 'SELECT value FROM workspace.probe;').strip() == '7'
        runner.cli('recreate-stop', 'down')
        runner.cli('recreate-start', 'up', timeout=240)
        after = {name: json.loads(execute('after-' + name, name, 'python', '-c', snapshot_code)) for name in ('opharma', 'sample')}
        assert before == after
        assert sql('recreate-preserved-sample', 'sample', 'SELECT value FROM workspace.probe;').strip() == '7'
        credentials_after = {p.relative_to(state).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in [*state.glob('*_password'), *state.glob('projects/*/password')]}
        assert credentials_before == credentials_after
        editor = runner.cli('editor-descriptor', 'project', 'editor', 'opharma').strip()
        runner.inventory(1, architecture)
        runner.summary.update(passed=True, repositories=after, separate_database_roles=True,
            cross_project_access_denied=True, scoped_reset_preserved_other_project=True,
            recreation_preserved_dirty_checkouts=True, credentials_preserved=True,
            bidirectional_host_mount=True, host_path_contains_spaces_and_dollar=True,
            editor_folder=editor, graphical_editor='NOT_EXECUTED')
    except (OSError, ValueError, RuntimeError, AssertionError, subprocess.SubprocessError) as error:
        runner.summary['error'] = str(error) or type(error).__name__
        print(runner.summary['error'], file=sys.stderr)
    finally:
        if owned and not (args.keep_running and runner.summary['passed']):
            try:
                runner.cli('stop-qualification', 'down')
                runner.summary['containers_removed_volumes_retained'] = True
            except (OSError, RuntimeError) as error:
                runner.summary.update(passed=False, cleanup_error=str(error))
        elif owned:
            runner.summary['kept_running_for_graphical_acceptance'] = True
        runner.summary['finished_at'] = runner.now()
        runner.save('qualification.json', runner.summary)
        print('Evidence: ' + str(output), flush=True)
    return 0 if runner.summary['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
