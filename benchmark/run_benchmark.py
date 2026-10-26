"""
Times logcrunch's serial vs. multi-process analysis on the large synthetic
log, across several worker counts, and writes the real measured results to
benchmark/results.csv. These are actual timings from this machine, not
estimated or invented numbers - run this yourself to reproduce them
(results will vary by machine/core count).
"""
import csv
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from logcrunch.parallel import analyze_file  # noqa: E402

LOG_PATH = os.path.join(os.path.dirname(__file__), "synthetic_large.log")
RESULTS_PATH = os.path.join(os.path.dirname(__file__), "results.csv")
WORKER_COUNTS = [1, 2, 4, 8]
REPEATS = 2  # average over 2 runs per worker count to smooth out noise


def main():
    if not os.path.exists(LOG_PATH):
        raise SystemExit("Run generate_synthetic_log.py first to create the benchmark file.")

    rows = []
    baseline = None
    for workers in WORKER_COUNTS:
        timings = []
        for _ in range(REPEATS):
            t0 = time.perf_counter()
            stats = analyze_file(LOG_PATH, workers)
            timings.append(time.perf_counter() - t0)
        avg = sum(timings) / len(timings)
        if baseline is None:
            baseline = avg
        speedup = baseline / avg
        rows.append(
            {
                "workers": workers,
                "avg_seconds": round(avg, 3),
                "speedup_vs_serial": round(speedup, 2),
                "lines_parsed": stats.total_lines,
            }
        )
        print(f"workers={workers:<3} avg={avg:.3f}s  speedup={speedup:.2f}x  (lines={stats.total_lines:,})")

    with open(RESULTS_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nWrote {RESULTS_PATH}")


if __name__ == "__main__":
    main()
