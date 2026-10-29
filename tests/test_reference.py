import importlib.util
from pathlib import Path
import sqlite3
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("reference", ROOT / "scripts/reference.py")
reference = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reference)


class ReplayEvidenceTests(unittest.TestCase):
    def test_snapshot_ignores_order_but_detects_duplicates_and_changed_values(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.sqlite"
            with sqlite3.connect(path) as connection:
                connection.executescript("CREATE TABLE facts(value); INSERT INTO facts VALUES (1), (2);")
            original = reference.database_snapshot(path)
            with sqlite3.connect(path) as connection:
                connection.executescript("DELETE FROM facts; INSERT INTO facts VALUES (2), (1);")
            self.assertEqual(original, reference.database_snapshot(path))
            with sqlite3.connect(path) as connection:
                connection.execute("INSERT INTO facts VALUES (1)")
            self.assertNotEqual(original, reference.database_snapshot(path))
            with sqlite3.connect(path) as connection:
                connection.executescript("DELETE FROM facts; INSERT INTO facts VALUES (1), (3);")
            self.assertNotEqual(original, reference.database_snapshot(path))


if __name__ == "__main__":
    unittest.main()
