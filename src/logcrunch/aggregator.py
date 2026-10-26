"""
Aggregation over a stream of LogRecords: counts by level, hourly volume,
top recurring message templates, and simple burst-based anomaly detection.

Designed so a partial aggregation (over one chunk of a file) and a final
aggregation (over the whole file) use the exact same data structure and can
be combined with `LogStats.merge()` - this is what lets the parallel path
(parallel.py) and the serial path produce identical results: each worker
builds one LogStats for its chunk, and the main process folds them together.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from statistics import mean, pstdev
from typing import Dict, Iterable, List, Tuple

from .parser import LogRecord
from .templater import to_template


@dataclass
class LogStats:
    total_lines: int = 0
    malformed_lines: int = 0
    level_counts: Counter = field(default_factory=Counter)
    hourly_counts: Counter = field(default_factory=Counter)  # key: "YYYY-MM-DD HH:00"
    hourly_level_counts: Counter = field(default_factory=Counter)  # key: (hour, level)
    template_counts: Counter = field(default_factory=Counter)

    def add_record(self, record: LogRecord) -> None:
        self.total_lines += 1
        self.level_counts[record.level] += 1
        hour_key = record.timestamp.strftime("%Y-%m-%d %H:00")
        self.hourly_counts[hour_key] += 1
        self.hourly_level_counts[(hour_key, record.level)] += 1
        self.template_counts[to_template(record.message)] += 1

    def add_malformed(self) -> None:
        self.malformed_lines += 1

    def merge(self, other: "LogStats") -> "LogStats":
        """Return a new LogStats combining self and other (does not mutate)."""
        merged = LogStats(
            total_lines=self.total_lines + other.total_lines,
            malformed_lines=self.malformed_lines + other.malformed_lines,
            level_counts=self.level_counts + other.level_counts,
            hourly_counts=self.hourly_counts + other.hourly_counts,
            hourly_level_counts=self.hourly_level_counts + other.hourly_level_counts,
            template_counts=self.template_counts + other.template_counts,
        )
        return merged

    def top_templates(self, n: int = 10) -> List[Tuple[str, int]]:
        return self.template_counts.most_common(n)

    def sorted_hours(self) -> List[str]:
        return sorted(self.hourly_counts.keys())

    def anomalous_hours(self, level: str = "error", z_threshold: float = 2.0) -> List[Dict]:
        """Flag hours whose count of `level` events is an outlier vs. the
        other hours in the file, using a simple z-score over hourly counts
        (mean + z_threshold * population-stdev). With too few distinct
        hours (<3) there isn't enough of a baseline to call anything an
        outlier, so this returns an empty list rather than a false signal.
        """
        hours = self.sorted_hours()
        counts = [self.hourly_level_counts.get((h, level), 0) for h in hours]
        if len(hours) < 3 or pstdev(counts) == 0:
            return []
        avg = mean(counts)
        sd = pstdev(counts)
        anomalies = []
        for hour, count in zip(hours, counts):
            z = (count - avg) / sd
            if z >= z_threshold:
                anomalies.append({"hour": hour, "count": count, "z_score": round(z, 2)})
        return sorted(anomalies, key=lambda a: -a["z_score"])

    def to_dict(self, top_n: int = 10, anomaly_level: str = "error") -> dict:
        return {
            "total_lines": self.total_lines,
            "malformed_lines": self.malformed_lines,
            "level_counts": dict(self.level_counts),
            "hours_covered": len(self.hourly_counts),
            "top_templates": self.top_templates(top_n),
            "anomalous_hours": self.anomalous_hours(level=anomaly_level),
        }


def aggregate(records: Iterable[LogRecord]) -> LogStats:
    stats = LogStats()
    for record in records:
        stats.add_record(record)
    return stats
