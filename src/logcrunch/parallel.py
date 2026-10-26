"""
Splits a log file into byte-range chunks (aligned to line boundaries) and
processes them across worker processes with multiprocessing.Pool, then
merges the per-chunk LogStats into one result.

Chunk alignment: a naive split-by-byte-offset would cut a line in half at
a chunk boundary. Instead, for each target offset we seek there, read and
discard the (partial) line we landed in the middle of, and use the
resulting file position - the start of the next full line - as the real
boundary. This guarantees every chunk contains only whole lines and the
parallel result is identical to the serial one (tests/test_parallel.py
checks this directly on real data).
"""
from __future__ import annotations

import multiprocessing
import os
from typing import List, Tuple

from .aggregator import LogStats
from .parser import ParseError, parse_line


def find_chunk_boundaries(path: str, num_chunks: int) -> List[Tuple[int, int]]:
    file_size = os.path.getsize(path)
    if num_chunks <= 1 or file_size == 0:
        return [(0, file_size)]

    approx_size = file_size / num_chunks
    cut_points = [0]
    with open(path, "rb") as f:
        for i in range(1, num_chunks):
            target = int(approx_size * i)
            if target >= file_size:
                break
            f.seek(target)
            f.readline()  # discard the partial line we landed inside
            pos = f.tell()
            if 0 < pos < file_size:
                cut_points.append(pos)
    cut_points.append(file_size)
    cut_points = sorted(set(cut_points))
    return list(zip(cut_points[:-1], cut_points[1:]))


def process_chunk(args: Tuple[str, int, int]) -> LogStats:
    """Parse and aggregate one byte range of a file. Module-level (not a
    closure/method) so it can be pickled and sent to worker processes."""
    path, start, end = args
    stats = LogStats()
    with open(path, "rb") as f:
        f.seek(start)
        data = f.read(end - start)
    text = data.decode("utf-8", errors="replace")
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            record = parse_line(line)
        except ParseError:
            stats.add_malformed()
            continue
        if record is not None:
            stats.add_record(record)
    return stats


def analyze_file_serial(path: str) -> LogStats:
    return process_chunk((path, 0, os.path.getsize(path)))


def analyze_file_parallel(path: str, num_workers: int) -> LogStats:
    chunks = find_chunk_boundaries(path, num_workers)
    if len(chunks) == 1:
        return process_chunk((path, *chunks[0]))

    tasks = [(path, start, end) for start, end in chunks]
    with multiprocessing.Pool(processes=len(tasks)) as pool:
        partial_results = pool.map(process_chunk, tasks)

    merged = LogStats()
    for partial in partial_results:
        merged = merged.merge(partial)
    return merged


def analyze_file(path: str, num_workers: int) -> LogStats:
    """Entry point used by the CLI: num_workers=1 takes the serial path."""
    if num_workers <= 1:
        return analyze_file_serial(path)
    return analyze_file_parallel(path, num_workers)
