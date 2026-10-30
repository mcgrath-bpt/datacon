"""Host-side failure and persistence checks; container acceptance is separate."""

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("datacon_cli", ROOT / "scripts/datacon.py")
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


class InstanceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def test_invalid_names_cannot_escape_instance_directory(self):
        for name in ("../other", "/tmp/other", "", "A", "a/b", "x; touch unexpected", "a" * 41):
            with self.subTest(name=name), self.assertRaises(cli.DataconError):
                cli.initialise(name, self.root)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_resume_preserves_credentials_and_dirty_work(self):
        state = cli.initialise("delivery-a", self.root)
        original = (state / "developer_password").read_bytes()
        work = state / "unfinished.txt"
        work.write_text("unfinished work")
        cli.initialise("delivery-a", self.root)
        self.assertEqual((state / "developer_password").read_bytes(), original)
        self.assertEqual(work.read_text(), "unfinished work")
        self.assertEqual(stat.S_IMODE(state.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((state / "developer_password").stat().st_mode), 0o444)
        self.assertNotEqual(original, (state / "postgres_password").read_bytes())

    def test_fresh_refuses_existing_state_and_keeps_it(self):
        state = cli.initialise("retained", self.root)
        before = {p.name: p.read_bytes() for p in state.iterdir()}
        with self.assertRaises(cli.DataconError):
            cli.initialise("retained", self.root, fresh=True)
        self.assertEqual({p.name: p.read_bytes() for p in state.iterdir()}, before)

    def test_missing_credentials_are_not_rotated_on_resume(self):
        state = cli.initialise("retained", self.root)
        (state / "developer_password").unlink()
        with self.assertRaises(cli.DataconError):
            cli.initialise("retained", self.root)
        self.assertFalse((state / "developer_password").exists())

    def test_instances_have_separate_credentials_and_namespaces(self):
        first = cli.initialise("a", self.root)
        second = cli.initialise("b", self.root)
        self.assertNotEqual(first, second)
        self.assertNotEqual((first / "developer_password").read_bytes(), (second / "developer_password").read_bytes())
        self.assertIn("datacon-a", cli.compose("a", "down", root=self.root))
        self.assertIn("datacon-b", cli.compose("b", "down", root=self.root))

    def test_retained_docker_volume_prevents_fresh_reuse(self):
        result = subprocess.CompletedProcess([], 0, stdout="datacon-kept_workspaces\n")
        with patch.object(cli, "run", return_value=result), self.assertRaises(cli.DataconError):
            cli.assert_unused("kept", {})

    def test_unlabelled_volume_prevents_reusing_lost_instance_state(self):
        empty = subprocess.CompletedProcess([], 0, stdout="")
        restored = subprocess.CompletedProcess([], 0, stdout="datacon-kept_workspaces\n")
        with patch.object(cli, "run", side_effect=[empty, empty, restored]), self.assertRaises(cli.DataconError):
            cli.assert_unused("kept", {})

    def test_initialise_entrypoint_refuses_existing_docker_data_before_writing(self):
        with patch.object(cli, "state_path", return_value=self.root / "absent"), \
             patch.object(cli, "assert_unused", side_effect=cli.DataconError("retained volumes")), \
             patch.object(cli, "initialise") as initialise, \
             contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(["init"]), 1)
        initialise.assert_not_called()


class CommandTests(unittest.TestCase):
    def test_down_never_requests_volume_deletion(self):
        with patch.object(cli, "run") as run:
            self.assertEqual(cli.main(["--instance", "retained", "down"]), 0)
        command = run.call_args.args[0]
        self.assertIn("datacon-retained", command)
        self.assertEqual(command[-1], "down")
        self.assertNotIn("--volumes", command)
        self.assertNotIn("-v", command)

    def test_exec_preserves_spaces_and_shell_characters_as_arguments(self):
        literal = "a b; $(touch unwanted)"
        with patch.object(cli, "run") as run:
            self.assertEqual(cli.main(["exec", "--", "printf", "%s", literal]), 0)
        self.assertEqual(run.call_args.args[0][-3:], ["printf", "%s", literal])

    def test_command_failure_reaches_caller(self):
        with patch.object(cli, "run", side_effect=subprocess.CalledProcessError(23, ["docker"])), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(["smoke"]), 23)

    def test_missing_daemon_is_a_failure_not_a_green_doctor(self):
        output = io.StringIO()
        with patch.object(cli, "probe", return_value=None), \
             patch.object(cli, "docker_status", return_value=({}, "unreachable")), \
             contextlib.redirect_stdout(output):
            self.assertEqual(cli.doctor("default", as_json=True), 1)
        report = json.loads(output.getvalue())
        self.assertFalse(report["daemon_available"])
        self.assertIn("Start Docker", report["next_step"])

    def test_denied_docker_access_does_not_advise_restarting_the_daemon(self):
        output = io.StringIO()
        with patch.object(cli, "probe", return_value=None), \
             patch.object(cli, "docker_status", return_value=({}, "access_denied")), \
             contextlib.redirect_stdout(output):
            self.assertEqual(cli.doctor("default", as_json=True), 1)
        report = json.loads(output.getvalue())
        self.assertEqual(report["docker_error"], "access_denied")
        self.assertIn("access is denied", report["next_step"])
        self.assertNotIn("Start Docker", report["next_step"])

    def test_missing_git_is_a_failure_with_an_actionable_diagnostic(self):
        output = io.StringIO()
        def probe(command):
            return '5.6.1' if command[:3] == ['docker', 'compose', 'version'] else None
        with patch.object(cli, 'probe', side_effect=probe), \
             patch.object(cli, 'docker_status', return_value=({'ServerVersion': '29.9.2'}, None)), \
             contextlib.redirect_stdout(output):
            self.assertEqual(cli.doctor('default', as_json=True), 1)
        self.assertIn('Install Git', json.loads(output.getvalue())['next_step'])

    def test_docker_error_classification_does_not_leak_credentials(self):
        error = subprocess.CalledProcessError(1, ["docker"], stderr="permission denied password=private-value")
        with patch.object(cli, "run", side_effect=error):
            self.assertEqual(cli.docker_status(), ({}, "access_denied"))

    def test_old_host_python_is_rejected_even_when_launcher_is_bypassed(self):
        with patch.object(cli.sys, "version_info", (3, 9, 6)), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(["config"]), 1)

    def test_doctor_does_not_expose_raw_docker_errors(self):
        error = subprocess.CalledProcessError(1, ["docker"], stderr="password=private-value")
        with patch.object(cli, "run", side_effect=error):
            self.assertIsNone(cli.probe(["docker", "info"]))

    def test_ambient_compose_profiles_do_not_start_extra_services(self):
        with patch.dict(os.environ, {"COMPOSE_PROFILES": "catalogue,extra"}):
            env = cli.environment("default")
        self.assertNotIn("COMPOSE_PROFILES", env)


if __name__ == "__main__":
    unittest.main()
