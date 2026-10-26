"""
Command-line entry point. After an editable install (`pip install -e .`)
this is runnable directly as `logcrunch`; it also works as
`python -m logcrunch` via __main__.py.
"""
from __future__ import annotations

import argparse
import json
import multiprocessing
import sys
import time

from .parallel import analyze_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logcrunch",
        description="Parse and analyze Apache-style error logs: level counts, "
        "hourly volume, recurring message templates, and anomalous error bursts.",
    )
    parser.add_argument("logfile", help="path to the log file to analyze")
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="number of worker processes (default: 1, i.e. serial). "
        "Use 0 to auto-detect the CPU count.",
    )
    parser.add_argument(
        "--top-n", type=int, default=10, help="number of top message templates to show (default: 10)"
    )
    parser.add_argument(
        "--anomaly-level",
        default="error",
        help="log level to run burst/anomaly detection on (default: error)",
    )
    parser.add_argument(
        "--format", choices=["text", "json"], default="text", help="output format (default: text)"
    )
    parser.add_argument(
        "--timing", action="store_true", help="print how long parsing+aggregation took"
    )
    return parser


def render_text(stats_dict: dict) -> str:
    lines = []
    lines.append(f"Lines parsed:     {stats_dict['total_lines']:,}")
    if stats_dict["malformed_lines"]:
        lines.append(f"Malformed lines:  {stats_dict['malformed_lines']:,} (skipped)")
    lines.append(f"Hours covered:    {stats_dict['hours_covered']:,}")
    lines.append("")
    lines.append("Level counts:")
    for level, count in sorted(stats_dict["level_counts"].items(), key=lambda kv: -kv[1]):
        lines.append(f"  {level:<10} {count:,}")
    lines.append("")
    lines.append(f"Top {len(stats_dict['top_templates'])} message templates:")
    for template, count in stats_dict["top_templates"]:
        lines.append(f"  {count:>6,}  {template}")
    anomalies = stats_dict["anomalous_hours"]
    lines.append("")
    if anomalies:
        lines.append(f"Anomalous hours ({stats_dict.get('_anomaly_level', 'error')} bursts, z >= 2.0):")
        for a in anomalies:
            lines.append(f"  {a['hour']}  count={a['count']}  z={a['z_score']}")
    else:
        lines.append("No anomalous hours detected.")
    return "\n".join(lines)


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    workers = args.workers
    if workers == 0:
        workers = multiprocessing.cpu_count()

    start_time = time.perf_counter()
    try:
        stats = analyze_file(args.logfile, workers)
    except FileNotFoundError:
        print(f"logcrunch: no such file: {args.logfile}", file=sys.stderr)
        return 1
    elapsed = time.perf_counter() - start_time

    stats_dict = stats.to_dict(top_n=args.top_n, anomaly_level=args.anomaly_level)
    stats_dict["_anomaly_level"] = args.anomaly_level

    if args.format == "json":
        print(json.dumps(stats_dict, indent=2))
    else:
        print(render_text(stats_dict))

    if args.timing:
        print(f"\n[workers={workers}] analyzed {stats.total_lines:,} lines in {elapsed:.3f}s", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
