"""
Generates a large, SYNTHETIC log file in the same format as the real
Apache error log (data_real/Apache_2k.log) for one purpose only: giving
the parallel benchmark (run_benchmark.py) enough volume to show a
measurable difference between serial and multi-process parsing. The real
2,000-line sample is too small for that - a benchmark needs millions of
lines to make processing time (not process start-up overhead) dominate.

This file is NOT used anywhere as a stand-in for real-world findings -
every analysis claim in the README is either run against the real log or
clearly labeled as a benchmark-only timing result. The message templates
and realistic error-burst injection below are modeled on the real sample's
actual template distribution (see data_real/Apache_2k.log), just repeated
and reshuffled at scale with randomized IDs/timestamps.
"""
from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta

random.seed(42)  # deterministic output, so benchmark runs are reproducible

NOTICE_TEMPLATES = [
    "jk2_init() Found child {n1} in scoreboard slot {n2}",
    "workerEnv.init() ok /etc/httpd/conf/workers2.properties",
    "jk2_init() Can't find child {n1} in scoreboard",
]
ERROR_TEMPLATES = [
    "mod_jk child workerEnv in error state {n1}",
    "mod_jk child init {n1} -{n2}",
    "[client {ip}] Directory index forbidden by rule: /var/www/html/",
]

# Real sample is ~70% notice / 30% error - matched here for realism.
LEVEL_WEIGHTS = [("notice", 0.70), ("error", 0.30)]


def random_ip() -> str:
    return ".".join(str(random.randint(1, 254)) for _ in range(4))


def render(level: str) -> str:
    template = random.choice(NOTICE_TEMPLATES if level == "notice" else ERROR_TEMPLATES)
    return template.format(n1=random.randint(1, 32000), n2=random.randint(1, 20), ip=random_ip())


def generate(num_lines: int, start: datetime, burst_hours: set[int]) -> "list[str]":
    lines = []
    timestamp = start
    for i in range(num_lines):
        # time advances a few seconds per line, on average
        timestamp += timedelta(seconds=random.randint(1, 6))
        hour_index = int((timestamp - start).total_seconds() // 3600)

        if hour_index in burst_hours:
            level = "error" if random.random() < 0.9 else "notice"  # injected burst hour
        else:
            level = random.choices(*zip(*LEVEL_WEIGHTS))[0]

        message = render(level)
        lines.append(f"[{timestamp.strftime('%a %b %d %H:%M:%S %Y')}] [{level}] {message}")
    return lines


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lines", type=int, default=2_000_000, help="number of lines to generate")
    parser.add_argument("--out", default="benchmark/synthetic_large.log")
    parser.add_argument(
        "--burst-hours",
        type=int,
        nargs="*",
        default=[10, 40],
        help="hour-indices (since start) to inject an error burst into, for testing anomaly detection at scale",
    )
    args = parser.parse_args()

    start = datetime(2026, 1, 1, 0, 0, 0)
    lines = generate(args.lines, start, set(args.burst_hours))
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Wrote {len(lines):,} synthetic lines to {args.out}")


if __name__ == "__main__":
    main()
