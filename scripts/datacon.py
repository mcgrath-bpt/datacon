#!/usr/bin/env python3
"""Dependency-free host entry point; stable Python 3.12+ on macOS or Linux/WSL."""

import argparse
import json
import os
from pathlib import Path
import platform
import re
import secrets
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
INSTANCE_PATTERN = re.compile(r"[a-z][a-z0-9-]{0,39}\Z")


class DataconError(Exception):
    pass


def instance_name(value):
    if not INSTANCE_PATTERN.fullmatch(value):
        raise DataconError("Instance names must start with a lower-case letter and contain at most 40 lower-case letters, digits or hyphens.")
    return value


def state_path(instance, root=ROOT):
    return root / ".local" / "instances" / instance_name(instance)


def initialise(instance, root=ROOT, fresh=False):
    state = state_path(instance, root)
    if fresh and state.exists():
        raise DataconError("That instance already has local state. Choose another name; use up to resume it.")
    if state.exists():
        # Never silently rotate a password for an existing database volume.
        for name in ("postgres_password", "developer_password"):
            path = state / name
            if not path.is_file() or not path.read_text().strip():
                raise DataconError("Instance credentials are incomplete. Restore them from your local backup or use a new instance name.")
        return state
    state.mkdir(mode=0o700, parents=True, exist_ok=False)
    for name in ("postgres_password", "developer_password"):
        path = state / name
        with path.open("x") as stream:
            # Compose file secrets are bind mounts: the container's non-root
            # users need read access. The containing host directory is 0700.
            os.chmod(path, 0o444)
            stream.write(secrets.token_urlsafe(32) + "\n")
    return state


def compose(instance, *arguments, root=ROOT):
    instance_name(instance)
    return ["docker", "compose", "--project-directory", str(root), "--project-name",
            "datacon-" + instance, "--file", str(root / "compose.yaml"), *arguments]


def environment(instance, root=ROOT):
    env = os.environ.copy()
    # Prevent ambient profile selection from starting unrelated service groups.
    env.pop("COMPOSE_PROFILES", None)
    env["DATACON_INSTANCE"] = instance_name(instance)
    env["DATACON_STATE_DIR"] = str(state_path(instance, root))
    return env


def run(command, env=None, capture=False, timeout=None):
    try:
        return subprocess.run(command, env=env, text=True, capture_output=capture,
                              timeout=timeout, check=True)
    except FileNotFoundError as error:
        raise DataconError("Required command is unavailable: " + command[0]) from error
    except subprocess.TimeoutExpired as error:
        raise DataconError("Command timed out: " + command[0]) from error


def probe(command):
    try:
        result = run(command, capture=True, timeout=10)
        return result.stdout.strip()
    except (DataconError, subprocess.CalledProcessError):
        # Diagnostic output must not expose connection strings or credentials.
        return None


def docker_status():
    """Classify Docker failures without returning raw diagnostics or secrets."""
    try:
        result = run(["docker", "info", "--format", "{{json .}}"], capture=True, timeout=10)
        info = json.loads(result.stdout)
        if not isinstance(info, dict) or not info.get("ServerVersion"):
            return {}, "invalid_response"
        return info, None
    except subprocess.CalledProcessError as error:
        message = (error.stderr or "").lower()
        if "permission denied" in message or "operation not permitted" in message:
            return {}, "access_denied"
        return {}, "unreachable"
    except DataconError as error:
        return {}, "timeout" if "timed out" in str(error) else "cli_unavailable"
    except ValueError:
        return {}, "invalid_response"


def doctor(instance, as_json=False):
    revision = probe(["git", "-C", str(ROOT), "rev-parse", "HEAD"])
    docker_version = probe(["docker", "--version"])
    compose_version = probe(["docker", "compose", "version", "--short"])
    info, docker_error = docker_status()
    report = {"instance": instance, "host": platform.system(), "architecture": platform.machine(),
              "host_python": platform.python_version(), "host_python_executable": sys.executable,
              "workspace_python_target": (ROOT / ".python-version").read_text().strip(), "platform_commit": revision,
              "docker_client": docker_version, "compose": compose_version,
              "daemon_available": bool(info), "docker_error": docker_error,
              "runtime_qualification": "NOT_EXECUTED"}
    if info:
        report.update(docker_server=info.get("ServerVersion"),
                      daemon_architecture=info.get("Architecture"), cpus=info.get("NCPU"),
                      memory_bytes=info.get("MemTotal"))
    if docker_error == "access_denied":
        report["next_step"] = "Docker access is denied to this process. Check session permissions or run from an authorised terminal; restarting Docker will not change a sandbox restriction."
    elif not report["daemon_available"]:
        report["next_step"] = "Start Docker Desktop or your Linux Docker daemon if needed. If it is already running, check the selected Docker context and this session's socket access."
    elif not compose_version:
        report["next_step"] = "Install a supported Docker Compose plugin."
    else:
        report["next_step"] = "Run up, smoke and reference. Resource and supported-host acceptance remain separate checks."
    if as_json:
        print(json.dumps(report, indent=2))
    else:
        for key, value in report.items():
            print(f"{key}: {value}")
    return 0 if report["daemon_available"] and compose_version else 1


def assert_unused(instance, env):
    for kind in ("container", "volume"):
        result = run(["docker", kind, "ls", *(["--all"] if kind == "container" else []),
                      "--filter", "label=com.docker.compose.project=datacon-" + instance,
                      "--format", "{{.Name}}" if kind == "volume" else "{{.Names}}"],
                     env=env, capture=True, timeout=15)
        if result.stdout.strip():
            raise DataconError("Docker already holds resources for this instance. Choose a new name; existing work has been preserved.")
    # Also protect volumes created/restored without Compose labels.
    result = run(["docker", "volume", "ls", "--format", "{{.Name}}"],
                 env=env, capture=True, timeout=15)
    if any(name.startswith("datacon-" + instance + "_") for name in result.stdout.splitlines()):
        raise DataconError("A named volume already uses this instance's prefix. Choose another name or restore its original credentials.")


def main(argv=None):
    if sys.version_info < (3, 12) or sys.version_info.releaselevel != "final":
        print("datacon: stable Python 3.12 or later is required. Use ./datacon to select an installed interpreter.", file=sys.stderr)
        return 1
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instance", default="default", help="Isolated workspace/database instance (default: default)")
    commands = parser.add_subparsers(dest="action", required=True)
    commands.add_parser("init", help="Create local credentials once; preserve existing credentials")
    diagnostic = commands.add_parser("doctor", help="Report prerequisites without exposing secrets")
    diagnostic.add_argument("--json", action="store_true")
    start = commands.add_parser("up", help="Build and start the core; resume persistent volumes")
    start.add_argument("--workspace-only", action="store_true")
    fresh = commands.add_parser("fresh", help="Start a new named instance without altering retained work")
    fresh.add_argument("name")
    fresh.add_argument("--workspace-only", action="store_true")
    commands.add_parser("config", help="Validate Compose configuration without starting containers")
    commands.add_parser("status", help="Show this instance's containers")
    commands.add_parser("down", help="Remove this instance's containers; preserve all named volumes")
    commands.add_parser("shell", help="Open a shell in the workspace")
    execute = commands.add_parser("exec", help="Execute a command in the workspace, after --")
    execute.add_argument("command", nargs=argparse.REMAINDER)
    commands.add_parser("smoke", help="Check non-root tools, database access, RLS and DuckDB execution")
    commands.add_parser("reference", help="Clone and test the pinned Opharma reference in a new checkout")
    commands.add_parser("check", help="Run host-side unit tests without Docker or network access")
    args = parser.parse_args(argv)
    try:
        instance = instance_name(args.name if args.action == "fresh" else args.instance)
        env = environment(instance)
        if args.action == "doctor":
            return doctor(instance, args.json)
        if args.action == "check":
            run([sys.executable, "-m", "unittest", "discover", "-s", str(ROOT / "tests"), "-v"])
            return 0
        if args.action == "init":
            if not state_path(instance).exists():
                assert_unused(instance, env)
            initialise(instance)
            print("Local credentials ready for " + instance + "; existing values preserved.")
            return 0
        if args.action in ("up", "fresh"):
            if args.action == "fresh" or not state_path(instance).exists():
                assert_unused(instance, env)
            initialise(instance, fresh=args.action == "fresh")
            services = ["workspace"] if args.workspace_only else ["workspace", "warehouse"]
            run(compose(instance, "up", "--detach", "--build", "--wait", "--wait-timeout", "120", *services), env=env)
            return 0
        if args.action == "config":
            run(compose(instance, "--profile", "core", "config", "--quiet"), env=env)
        elif args.action == "status":
            run(compose(instance, "--profile", "core", "ps", "--all"), env=env)
        elif args.action == "down":
            run(compose(instance, "--profile", "*", "down"), env=env)
        else:
            if args.action == "shell":
                command = ["bash"]
            elif args.action == "exec":
                command = args.command[1:] if args.command[:1] == ["--"] else args.command
                if not command:
                    raise DataconError("Provide a command after exec --.")
            else:
                command = ["/opt/datacon/venv/bin/python", "/opt/datacon/scripts/" + args.action + ".py"]
            flags = [] if sys.stdin.isatty() and args.action in ("shell", "exec") else ["-T"]
            run(compose(instance, "exec", *flags, "workspace", *command), env=env)
        return 0
    except DataconError as error:
        print("datacon: " + str(error), file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as error:
        print(f"datacon: command failed with exit status {error.returncode}.", file=sys.stderr)
        if error.cmd and error.cmd[0] == "docker":
            print("Run ./datacon doctor to check Docker availability and session access.", file=sys.stderr)
        return error.returncode if 0 < error.returncode < 126 else 1
    except OSError as error:
        print("datacon: filesystem operation failed: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
