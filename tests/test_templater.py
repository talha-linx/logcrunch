import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from logcrunch.templater import to_template  # noqa: E402


class TemplaterTests(unittest.TestCase):
    def test_collapses_numbers(self):
        a = to_template("jk2_init() Found child 32710 in scoreboard slot 9")
        b = to_template("jk2_init() Found child 5998 in scoreboard slot 6")
        self.assertEqual(a, b)
        self.assertEqual(a, "jk2_init() Found child <NUM> in scoreboard slot <NUM>")

    def test_collapses_hex(self):
        self.assertEqual(to_template("ptr 0x1A2B freed"), "ptr <HEX> freed")

    def test_leaves_non_numeric_text_untouched(self):
        self.assertEqual(to_template("workerEnv.init() ok"), "workerEnv.init() ok")


if __name__ == "__main__":
    unittest.main()
