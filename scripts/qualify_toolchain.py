#!/usr/bin/env python3
"""Qualify the optional toolchain twice on native ARM64/AMD64; retain instance data."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess
import sys
import uuid

import baseline
import datacon
from qualify import Qualification, assert_native, compare_inventories

ROOT = Path(__file__).resolve().parents[1]


class ToolchainQualification(Qualification):
    def execute(self, expected_architecture=None):
        owned = False
        try:
            self.save('qualification.json', self.summary)
            self.summary['platform_commit'] = self.run('revision', ['git', 'rev-parse', 'HEAD']).strip()
            self.summary['working_tree'] = self.run('working-tree', ['git', 'status', '--porcelain'])
            self.summary['baseline'] = baseline.identity()
            doctor = json.loads(self.cli('doctor', 'doctor', '--json'))
            architecture = assert_native(platform.machine(), doctor['daemon_architecture'], expected_architecture)
            self.summary.update(architecture=architecture, native=True)
            if datacon.state_path(self.instance).exists():
                raise ValueError('Qualification refuses existing local state')
            self.cli('initialise', 'init')
            owned = True
            self.secrets = [p.read_text().strip() for p in datacon.state_path(self.instance).glob('*_password')]
            self.compose('warehouse-start', 'up', '--detach', '--wait', 'warehouse', timeout=240)
            inventories = []
            for iteration in (1, 2):
                prefix = 'build-' + str(iteration)
                self.compose(prefix, 'build', '--pull', '--no-cache', 'toolchain', timeout=720)
                image_name = 'datacon-' + self.instance + '-toolchain'
                image = json.loads(self.run(prefix + '-image', ['docker', 'image', 'inspect', '--format',
                    '{"id":{{json .Id}},"architecture":{{json .Architecture}},"size_bytes":{{json .Size}}}', image_name]))
                if image['architecture'] != architecture:
                    raise ValueError('Toolchain image architecture mismatch')
                self.save(prefix + '-identity.json', image)
                command = ['run', '--rm', '--no-deps', '-T', 'toolchain']
                self.compose(prefix + '-pip-check', *command, 'python', '-m', 'pip', 'check')
                code = """import importlib.metadata,json,os,platform,subprocess
print(json.dumps({'python':platform.python_version(),'architecture':platform.machine(),'uid':os.getuid(),
 'packages':sorted([(d.metadata['Name'],d.version) for d in importlib.metadata.distributions()]),
 'os':subprocess.check_output(['dpkg-query','-W','-f=${binary:Package}\\t${Version}\\t${Architecture}\\n'],text=True)}))
"""
                inventory = json.loads(self.compose(prefix + '-inventory', *command, 'python', '-c', code))
                if inventory['python'] != '3.14.8' or inventory['uid'] == 0:
                    raise ValueError('Toolchain interpreter or user mismatch')
                assert_native(inventory['architecture'], architecture, expected_architecture)
                inventories.append(inventory)
                self.save(prefix + '-inventory.json', inventory)
                self.run(prefix + '-offline', ['docker', 'run', '--rm', '--network', 'none', image['id'],
                    'python', '/opt/datacon/scripts/toolchain_smoke.py', '--offline'])
                self.compose(prefix + '-smoke', *command)
                if iteration == 1:
                    code = """from pathlib import Path
import subprocess,sys,tempfile
with tempfile.TemporaryDirectory() as directory:
 p=Path(directory)/'bad.txt'
 p.write_text('attrs==26.1.0 --hash=sha256:'+'0'*64+'\\n')
 sys.exit(subprocess.call([sys.executable,'-m','pip','install','--ignore-installed','--no-deps',
  '--no-cache-dir','--only-binary=:all:','--require-hashes','--target',directory+'/packages','-r',str(p)]))
"""
                    self.compose('reject-toolchain-wheel-hash', *command, 'python', '-c', code,
                                 expected_failure='DO NOT MATCH THE HASHES')
            compare_inventories(*inventories)
            self.summary.update(passed=True, repeated_inventories_identical=True, negative_checks_passed=True,
                                snowflake_native='NOT_EXECUTED; DC-014–DC-016 require a target account')
        except (OSError, ValueError, RuntimeError, KeyError, subprocess.SubprocessError) as error:
            self.summary['error'] = str(error)
            print(str(error), file=sys.stderr)
        finally:
            if owned:
                try:
                    self.cli('stop-qualification', 'down', timeout=120)
                    self.summary['containers_removed_volumes_retained'] = True
                except (OSError, RuntimeError) as error:
                    self.summary.update(passed=False, cleanup_error=str(error))
            self.summary['finished_at'] = self.now()
            self.save('qualification.json', self.summary)
        return 0 if self.summary['passed'] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--expected-architecture', choices=('arm64', 'amd64'))
    args = parser.parse_args()
    if sys.version_info < (3, 12) or sys.version_info.releaselevel != 'final':
        parser.error('stable host Python 3.12 or later is required')
    instance = 'tools-' + datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S') + '-' + uuid.uuid4().hex[:6]
    output = (args.output or ROOT / '.local/toolchain-qualification' / instance).resolve()
    output.mkdir(parents=True, exist_ok=False)
    print('Qualification evidence: ' + str(output), flush=True)
    return ToolchainQualification(output, instance).execute(args.expected_architecture)


if __name__ == '__main__':
    sys.exit(main())
