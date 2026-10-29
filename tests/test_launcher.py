"""Exercise the real shell selector with controlled Python executables."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="datacon launcher ")
        self.addCleanup(self.directory.cleanup)
        self.bin = Path(self.directory.name)
        self.env = os.environ.copy()
        self.env.pop("DATACON_PYTHON", None)
        self.env["PATH"] = str(self.bin) + ":/usr/bin:/bin"
        for name in ("python3.15", "python3.14", "python3.13", "python3.12", "python3"):
            self.python(name, supported=False)

    def python(self, name, supported):
        path = self.bin / name
        path.write_text('#!/bin/sh\nif [ "$1" = "-c" ]; then exit ' + ("0" if supported else "1")
                        + '; fi\nprintf "%s\\n" "$0" "$@"\n')
        path.chmod(0o755)
        return path

    def launch(self):
        return subprocess.run(["/bin/sh", str(ROOT / "datacon"), "config"], env=self.env,
                              capture_output=True, text=True, check=False)

    def test_prefers_newest_supported_named_interpreter(self):
        preferred = self.python("python3.15", supported=True)
        self.python("python3.14", supported=True)
        result = self.launch()
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.splitlines()[0], str(preferred))

    def test_skips_unsupported_interpreters(self):
        supported = self.python("python3.14", supported=True)
        result = self.launch()
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.splitlines()[0], str(supported))

    def test_refuses_to_fall_back_below_the_minimum(self):
        result = self.launch()
        self.assertEqual(result.returncode, 1)
        self.assertIn("Python 3.12 or later", result.stderr)

    def test_explicit_override_with_spaces_is_preserved(self):
        executable = self.python("selected python", supported=True)
        self.env["DATACON_PYTHON"] = str(executable)
        result = self.launch()
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.splitlines()[0], str(executable))

    def test_invalid_override_fails_without_silent_fallback(self):
        self.python("python3.15", supported=True)
        self.env["DATACON_PYTHON"] = str(self.bin / "python3")
        result = self.launch()
        self.assertEqual(result.returncode, 1)
        self.assertIn("DATACON_PYTHON", result.stderr)
