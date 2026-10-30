#!/usr/bin/env python3
"""Qualify core on the native host/daemon architecture; retain all named volumes."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import uuid

import datacon

ROOT = Path(__file__).resolve().parents[1]
ARCHITECTURES = {"aarch64": "arm64", "arm64": "arm64", "x86_64": "amd64", "amd64": "amd64"}
REFERENCE_FILES = ("tests.json", "first-run.json", "replay.json", "summary.json")


def sanitise(value, secrets=()):
    for secret in secrets:
        if secret:
            value = value.replace(secret, "[REDACTED]")
    value = re.sub(r"(https?://)[^/\s@]+@", r"\1[REDACTED]@", value)
    return re.sub(r"(?i)(password|token|authorization)(\s*[=:]\s*)[^\s,\"']+",
                  r"\1\2[REDACTED]", value)


def assert_native(host, daemon, expected=None):
    host, daemon = ARCHITECTURES.get(host), ARCHITECTURES.get(daemon)
    if not host or host != daemon or (expected and daemon != expected):
        raise ValueError("Native qualification requires matching supported host and daemon architectures")
    return daemon


def compare_inventories(first, second):
    if first != second:
        raise ValueError("Repeated clean builds produced different dependency inventories")


class Qualification:
    def __init__(self, output, instance):
        self.output, self.instance = output, instance
        self.env = datacon.environment(instance)
        # No implicit architecture override or ambient Compose files/build switches.
        for key in tuple(self.env):
            if key.startswith("COMPOSE_") or key in ("DOCKER_DEFAULT_PLATFORM", "BUILDX_BUILDER"):
                self.env.pop(key)
        self.env["BUILDKIT_PROGRESS"] = "plain"
        self.secrets = []
        self.summary = {"instance": instance, "started_at": self.now(), "passed": False, "steps": []}

    @staticmethod
    def now():
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def save(self, name, value):
        content = json.dumps(value, indent=2) + "\n" if not isinstance(value, str) else value
        (self.output / name).write_text(sanitise(content, self.secrets))

    def run(self, label, command, timeout=600, expected_failure=None):
        print(label, flush=True)
        started = self.now()
        try:
            result = subprocess.run(command, cwd=ROOT, env=self.env, text=True,
                                    capture_output=True, timeout=timeout)
        except subprocess.TimeoutExpired as error:
            partial = error.stdout or b""
            if isinstance(partial, bytes):
                partial = partial.decode(errors="replace")
            self.save(label + ".txt", partial + "\nCommand timed out\n")
            raise RuntimeError(label + " timed out") from error
        combined = result.stdout + result.stderr
        self.save(label + ".txt", combined)
        self.summary["steps"].append({"name": label, "started_at": started,
                                      "finished_at": self.now(), "exit_code": result.returncode})
        self.save("qualification.json", self.summary)
        if expected_failure:
            if result.returncode == 0 or expected_failure not in combined:
                raise RuntimeError(label + " did not fail for the expected integrity error")
        elif result.returncode:
            raise RuntimeError(label + " failed; see its sanitised transcript")
        return result.stdout

    def cli(self, label, *arguments, **kwargs):
        return self.run(label, [str(ROOT / "datacon"), "--instance", self.instance, *arguments], **kwargs)

    def compose(self, label, *arguments, **kwargs):
        return self.run(label, datacon.compose(self.instance, *arguments), **kwargs)

    def inventory(self, iteration, architecture):
        prefix = "build-" + str(iteration)
        self.cli(prefix + "-os-check", "exec", "--", "python", "/opt/datacon/scripts/verify_os.py")
        os_packages = self.cli(prefix + "-workspace-os", "exec", "--", "python",
                               "/opt/datacon/scripts/verify_os.py", "--inventory")
        packages = json.loads(self.cli(prefix + "-python-packages", "exec", "--",
                                       "python", "-m", "pip", "list", "--format=json"))
        versions = json.loads(self.cli(prefix + "-versions", "exec", "--", "python", "-c",
            "import json,platform,os; print(json.dumps({'python':platform.python_version(),"
            "'architecture':platform.machine(),'uid':os.getuid()}))"))
        if versions["python"] != (ROOT / ".python-version").read_text().strip() or versions["uid"] == 0:
            raise ValueError("Python version or non-root identity mismatch")
        if ARCHITECTURES.get(versions["architecture"]) != architecture:
            raise ValueError("Workspace architecture differs from the native daemon")
        warehouse = self.compose(prefix + "-warehouse-os", "exec", "-T", "warehouse", "dpkg-query", "-W",
                                 "-f=${binary:Package}\t${Version}\t${Architecture}\t${db:Status-Status}\n")
        self.compose(prefix + "-database-version", "exec", "-T", "warehouse", "psql", "-U", "postgres",
                     "-d", "datacon", "-X", "-qAt", "-c", "SELECT version(); SELECT extversion FROM pg_extension WHERE extname = 'pg_duckdb';")
        identities = {}
        for service in ("workspace", "warehouse"):
            cid = self.compose(prefix + "-" + service + "-id", "ps", "-q", service).strip()
            details = json.loads(self.run(prefix + "-" + service + "-identity", ["docker", "inspect", "--format",
                '{"image":{{json .Image}},"restart":{{json .HostConfig.RestartPolicy.Name}},"status":{{json .State.Status}}}', cid]))
            if details["restart"] != "unless-stopped" or details["status"] != "running":
                raise ValueError("Service lifecycle policy mismatch: " + service)
            image = json.loads(self.run(prefix + "-" + service + "-image", ["docker", "image", "inspect", "--format",
                '{"id":{{json .Id}},"architecture":{{json .Architecture}},"digests":{{json .RepoDigests}}}', details["image"]]))
            if image["architecture"] != architecture:
                raise ValueError("Image architecture differs from the native daemon")
            identities[service] = {**details, **image}
        self.save(prefix + "-identities.json", identities)
        result = {"workspace_os": os_packages, "python": sorted(packages, key=lambda p: p["name"]),
                  "warehouse_os": "\n".join(sorted(warehouse.splitlines())), "versions": versions}
        self.save(prefix + "-inventories.json", result)
        return result

    def collect_reference(self, iteration):
        # A fresh qualification volume contains only runner-created evidence. Explicit
        # filenames prevent copying SQLite databases, fixture trees or credentials.
        code = ("import json; from pathlib import Path; base=Path('/workspaces/.datacon-evidence'); "
                "print(json.dumps({p.name:{n:(p/n).read_text() for n in " + repr(REFERENCE_FILES) +
                " if (p/n).is_file()} for p in sorted(base.glob('opharma-*')) if p.is_dir()}))")
        output = self.cli("build-" + str(iteration) + "-reference-reports", "exec", "--", "python", "-c", code)
        self.save("build-" + str(iteration) + "-reference.json", json.loads(output))

    def negative_checks(self, architecture):
        # Exercise the actual Dockerfile OS gate with one changed lock entry.
        with tempfile.TemporaryDirectory(prefix="datacon-bad-lock-") as temporary:
            context = Path(temporary)
            for name in ("requirements/os", "scripts"):
                (context / name).mkdir(parents=True)
            for path in (ROOT / "requirements/os").iterdir():
                shutil.copy2(path, context / "requirements/os" / path.name)
            shutil.copy2(ROOT / "scripts/verify_os.py", context / "scripts/verify_os.py")
            shutil.copy2(ROOT / ".devcontainer/Dockerfile", context / "Dockerfile")
            lock = context / "requirements/os" / ("bookworm-" + architecture + ".tsv")
            lock.write_text(lock.read_text().replace("\t", "-deliberately-wrong\t", 1))
            self.run("reject-os-inventory", ["docker", "build", "--target", "os-locked", str(context)],
                     expected_failure="OS inventory mismatch")
        # Force a download/install check even though attrs is already installed.
        code = """from pathlib import Path
import subprocess, sys, tempfile
with tempfile.TemporaryDirectory() as directory:
    lock = Path(directory) / 'bad.txt'
    lock.write_text('attrs==25.4.0 --hash=sha256:' + '0'*64 + '\\n')
    result = subprocess.run([sys.executable, '-m', 'pip', 'install', '--ignore-installed',
        '--no-deps', '--no-cache-dir', '--only-binary=:all:', '--require-hashes',
        '--target', directory + '/packages', '-r', str(lock)])
    sys.exit(result.returncode)
"""
        self.cli("reject-wheel-hash", "exec", "--", "python", "-c", code,
                 expected_failure="DO NOT MATCH THE HASHES")
        self.summary["negative_checks_passed"] = True

    def execute(self, expected_architecture=None):
        owned = False
        try:
            self.save("qualification.json", self.summary)
            self.summary["platform_commit"] = self.run("revision", ["git", "rev-parse", "HEAD"]).strip()
            self.summary["working_tree"] = self.run("working-tree", ["git", "status", "--porcelain"])
            self.summary["input_sha256"] = {
                str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                for pattern in (".devcontainer/Dockerfile", "compose.yaml", ".python-version", "requirements/**/*",
                                "scripts/*.py", "platform/*.json")
                for p in sorted(ROOT.glob(pattern)) if p.is_file()}
            report = json.loads(self.cli("doctor", "doctor", "--json"))
            architecture = assert_native(platform.machine(), report["daemon_architecture"], expected_architecture)
            self.summary.update(architecture=architecture, native=True)
            self.cli("host-tests", "check")
            self.cli("compose-validation", "config")
            self.run("documentation", [sys.executable, str(ROOT / "scripts/check_docs.py")])
            self.run("whitespace", ["git", "diff", "--check"])
            if datacon.state_path(self.instance).exists():
                raise ValueError("Qualification refuses existing local state")
            self.cli("initialise", "init")
            owned = True
            self.secrets = [p.read_text().strip() for p in datacon.state_path(self.instance).glob('*_password')]
            inventories = []
            for iteration in (1, 2):
                prefix = "build-" + str(iteration)
                self.compose(prefix, "build", "--pull", "--no-cache", "workspace", timeout=720)
                self.cli(prefix + "-start", "up", timeout=240)
                self.cli(prefix + "-ready", "doctor", "--json", "--require-ready")
                inventories.append(self.inventory(iteration, architecture))
                self.cli(prefix + "-smoke", "smoke")
                try:
                    self.cli(prefix + "-reference", "reference", timeout=600)
                finally:
                    self.collect_reference(iteration)
                if iteration == 1:
                    self.negative_checks(architecture)
            compare_inventories(*inventories)
            self.summary.update(repeated_inventories_identical=True, passed=True)
        except (OSError, ValueError, RuntimeError, KeyError, subprocess.SubprocessError) as error:
            self.summary["error"] = str(error)
            print(sanitise(str(error), self.secrets), file=sys.stderr)
        finally:
            if owned:
                try:
                    self.cli("stop-qualification", "down", timeout=120)
                    self.summary["containers_removed_volumes_retained"] = True
                except (OSError, RuntimeError) as error:
                    self.summary.update(passed=False, cleanup_error=str(error))
            self.summary["finished_at"] = self.now()
            self.save("qualification.json", self.summary)
        return 0 if self.summary["passed"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="New evidence directory; never an existing directory")
    parser.add_argument("--expected-architecture", choices=("arm64", "amd64"))
    args = parser.parse_args()
    if sys.version_info < (3, 12) or sys.version_info.releaselevel != "final":
        parser.error("stable host Python 3.12 or later is required")
    instance = "qual-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S") + "-" + uuid.uuid4().hex[:8]
    output = (args.output or ROOT / ".local/qualification" / instance).resolve()
    output.mkdir(parents=True, exist_ok=False)
    print("Qualification evidence: " + str(output), flush=True)
    return Qualification(output, instance).execute(args.expected_architecture)


if __name__ == "__main__":
    sys.exit(main())
