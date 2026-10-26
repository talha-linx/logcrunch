import json
import os
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from logcrunch.cli import main  # noqa: E402

REAL_LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "data_real", "Apache_2k.log")


class CliTests(unittest.TestCase):
    def test_text_output_runs_cleanly(self):
        buf = StringIO()
        with redirect_stdout(buf):
            exit_code = main([REAL_LOG_PATH])
        self.assertEqual(exit_code, 0)
        self.assertIn("Lines parsed:", buf.getvalue())

    def test_json_output_is_valid_and_matches_real_totals(self):
        buf = StringIO()
        with redirect_stdout(buf):
            main([REAL_LOG_PATH, "--format", "json"])
        data = json.loads(buf.getvalue())
        self.assertEqual(data["total_lines"], 2000)
        self.assertEqual(data["level_counts"]["notice"], 1405)
        self.assertEqual(data["level_counts"]["error"], 595)

    def test_missing_file_returns_error_exit_code(self):
        buf = StringIO()
        with redirect_stdout(buf):
            exit_code = main(["/no/such/file.log"])
        self.assertEqual(exit_code, 1)

    def test_workers_flag_gives_same_totals_as_default(self):
        buf_serial, buf_parallel = StringIO(), StringIO()
        with redirect_stdout(buf_serial):
            main([REAL_LOG_PATH, "--format", "json"])
        with redirect_stdout(buf_parallel):
            main([REAL_LOG_PATH, "--format", "json", "--workers", "4"])
        serial_data = json.loads(buf_serial.getvalue())
        parallel_data = json.loads(buf_parallel.getvalue())
        self.assertEqual(serial_data["total_lines"], parallel_data["total_lines"])
        self.assertEqual(serial_data["level_counts"], parallel_data["level_counts"])


if __name__ == "__main__":
    unittest.main()
