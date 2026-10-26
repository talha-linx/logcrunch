import os
import sys
import unittest
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from logcrunch.parser import ParseError, parse_line, parse_lines  # noqa: E402

REAL_LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "data_real", "Apache_2k.log")


class ParserTests(unittest.TestCase):
    def test_parses_notice_line(self):
        line = "[Sun Dec 04 04:47:44 2005] [notice] workerEnv.init() ok /etc/httpd/conf/workers2.properties"
        record = parse_line(line)
        self.assertEqual(record.level, "notice")
        self.assertEqual(record.timestamp, datetime(2005, 12, 4, 4, 47, 44))
        self.assertIn("workerEnv.init()", record.message)

    def test_parses_error_line(self):
        line = "[Sun Dec 04 16:41:22 2005] [error] mod_jk child workerEnv in error state 6"
        record = parse_line(line)
        self.assertEqual(record.level, "error")
        self.assertEqual(record.message, "mod_jk child workerEnv in error state 6")

    def test_blank_line_returns_none(self):
        self.assertIsNone(parse_line("\n"))
        self.assertIsNone(parse_line(""))

    def test_malformed_line_raises(self):
        with self.assertRaises(ParseError):
            parse_line("this is not a log line at all")

    def test_parse_lines_skips_blanks_only(self):
        lines = [
            "[Sun Dec 04 04:47:44 2005] [notice] a\n",
            "\n",
            "[Sun Dec 04 04:47:45 2005] [error] b\n",
        ]
        records = list(parse_lines(lines))
        self.assertEqual(len(records), 2)
        self.assertEqual([r.level for r in records], ["notice", "error"])

    def test_against_real_sample_file(self):
        # Validates the parser against real, unmodified log data (not
        # synthetic) - 2,000 lines from a production Apache server, from
        # the loghub research dataset (github.com/logpai/loghub).
        with open(REAL_LOG_PATH, encoding="utf-8") as f:
            records = list(parse_lines(f))
        self.assertEqual(len(records), 2000)
        levels = {r.level for r in records}
        self.assertEqual(levels, {"notice", "error"})


if __name__ == "__main__":
    unittest.main()
