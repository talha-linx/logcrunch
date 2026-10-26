"""
Renders benchmark/results.csv (real measured timings, not invented numbers)
as a simple bar chart: average time per worker count, with the measured
speedup labeled on each bar. Single-hue sequential color (one metric, no
categorical comparison needed) per the house dataviz conventions used
across these portfolio projects.
"""
import csv
import os

import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS_PATH = os.path.join(HERE, "results.csv")
OUT_PATH = os.path.join(HERE, "benchmark_chart.png")

ACCENT = "#3987e5"  # mid-step of the validated sequential blue ramp used elsewhere
INK = "#2b2b28"
MUTED = "#6b6a66"
GRID = "#e4e3de"


def main():
    with open(RESULTS_PATH) as f:
        rows = list(csv.DictReader(f))

    workers = [r["workers"] for r in rows]
    seconds = [float(r["avg_seconds"]) for r in rows]
    speedups = [float(r["speedup_vs_serial"]) for r in rows]

    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=150)
    fig.patch.set_facecolor("#fcfcfb")
    ax.set_facecolor("#fcfcfb")

    bars = ax.bar(workers, seconds, color=ACCENT, width=0.55, zorder=3)

    for bar, s, sp in zip(bars, seconds, speedups):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.6,
            f"{s:.1f}s\n({sp:.2f}x)",
            ha="center",
            va="bottom",
            fontsize=9,
            color=INK,
        )

    ax.set_xlabel("worker processes", color=MUTED, fontsize=10)
    ax.set_ylabel("avg. time to parse 2,000,000 lines (s)", color=MUTED, fontsize=10)
    ax.set_title("logcrunch: parallel speedup on a 2-core sandbox", color=INK, fontsize=13, pad=14)
    ax.set_xticks(range(len(workers)))
    ax.set_xticklabels(workers)
    ax.set_ylim(0, max(seconds) * 1.22)

    ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUTED, length=0)

    fig.tight_layout()
    fig.savefig(OUT_PATH, facecolor=fig.get_facecolor())
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
