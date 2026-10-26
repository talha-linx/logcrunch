import os
import sys
import unittest
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from logcrunch.aggregator import LogStats, aggregate  # noqa: E402
from logcrunch.parser import LogRecord  # noqa: E402


def record(hour, minute, level, message):
    return LogRecord(
        timestamp=datetime(2024, 1, 1, hour, minute, 0),
        level=level,
        message=message,
        raw="",
    )


class AggregatorTests(unittest.TestCase):
    def test_level_counts(self):
        records = [
            record(10, 0, "notice", "a"),
            record(10, 1, "error", "b 1"),
            record(10, 2, "error", "b 2"),
        ]
        stats = aggregate(records)
        self.assertEqual(stats.level_counts["notice"], 1)
        self.assertEqual(stats.level_counts["error"], 2)
        self.assertEqual(stats.total_lines, 3)

    def test_templates_group_similar_messages(self):
        records = [
            record(10, 0, "error", "child 1 failed"),
            record(10, 1, "error", "child 99 failed"),
            record(10, 2, "notice", "all good"),
        ]
        stats = aggregate(records)
        top = dict(stats.top_templates())
        self.assertEqual(top["child <NUM> failed"], 2)
        self.assertEqual(top["all good"], 1)

    def test_merge_matches_single_pass_aggregation(self):
        records = [
            record(10, 0, "notice", "a"),
            record(11, 0, "error", "b 1"),
            record(12, 0, "error", "b 2"),
            record(12, 1, "notice", "c"),
        ]
        whole = aggregate(records)

        half_a = aggregate(records[:2])
        half_b = aggregate(records[2:])
        merged = half_a.merge(half_b)

        self.assertEqual(merged.total_lines, whole.total_lines)
        self.assertEqual(merged.level_counts, whole.level_counts)
        self.assertEqual(merged.hourly_counts, whole.hourly_counts)
        self.assertEqual(merged.template_counts, whole.template_counts)

    def test_anomalous_hours_needs_at_least_three_hours(self):
        stats = LogStats()
        stats.add_record(record(10, 0, "error", "x"))
        stats.add_record(record(11, 0, "error", "x"))
        self.assertEqual(stats.anomalous_hours(), [])

    def test_anomalous_hours_flags_a_real_burst(self):
        stats = LogStats()
        # five quiet hours with 1 error each, then one hour with a burst of 50
        for h in range(5):
            stats.add_record(record(h, 0, "error", "quiet"))
        for i in range(50):
            stats.add_record(record(23, i % 60, "error", "burst"))
        anomalies = stats.anomalous_hours(level="error")
        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0]["count"], 50)


if __name__ == "__main__":
    unittest.main()
