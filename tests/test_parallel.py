import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from logcrunch.parallel import (  # noqa: E402
    analyze_file_parallel,
    analyze_file_serial,
    find_chunk_boundaries,
)

REAL_LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "data_real", "Apache_2k.log")


class ChunkBoundaryTests(unittest.TestCase):
    def test_boundaries_cover_whole_file_with_no_gaps_or_overlaps(self):
        boundaries = find_chunk_boundaries(REAL_LOG_PATH, 5)
        file_size = os.path.getsize(REAL_LOG_PATH)
        self.assertEqual(boundaries[0][0], 0)
        self.assertEqual(boundaries[-1][1], file_size)
        for (_, end_a), (start_b, _) in zip(boundaries, boundaries[1:]):
            self.assertEqual(end_a, start_b)  # no gap, no overlap

    def test_every_chunk_starts_at_a_line_boundary(self):
        boundaries = find_chunk_boundaries(REAL_LOG_PATH, 5)
        with open(REAL_LOG_PATH, "rb") as f:
            data = f.read()
        for start, _ in boundaries[1:]:
            # the byte just before a non-zero chunk start must be a newline
            self.assertEqual(data[start - 1 : start], b"\n")

    def test_single_worker_returns_one_chunk_spanning_the_file(self):
        boundaries = find_chunk_boundaries(REAL_LOG_PATH, 1)
        self.assertEqual(len(boundaries), 1)
        self.assertEqual(boundaries[0], (0, os.path.getsize(REAL_LOG_PATH)))

    def test_more_workers_than_lines_does_not_crash(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("[Sun Dec 04 04:47:44 2005] [notice] only one line\n")
            path = f.name
        try:
            boundaries = find_chunk_boundaries(path, 50)
            self.assertGreaterEqual(len(boundaries), 1)
        finally:
            os.unlink(path)


class ParallelCorrectnessTests(unittest.TestCase):
    """The whole point of chunked parallelism is that it must produce the
    exact same answer as the serial path - these tests prove that on real
    log data, not just on a toy example."""

    def test_parallel_matches_serial_on_real_log(self):
        serial = analyze_file_serial(REAL_LOG_PATH)
        for workers in (2, 3, 4, 8):
            parallel = analyze_file_parallel(REAL_LOG_PATH, workers)
            self.assertEqual(parallel.total_lines, serial.total_lines)
            self.assertEqual(parallel.malformed_lines, serial.malformed_lines)
            self.assertEqual(dict(parallel.level_counts), dict(serial.level_counts))
            self.assertEqual(dict(parallel.hourly_counts), dict(serial.hourly_counts))
            self.assertEqual(dict(parallel.template_counts), dict(serial.template_counts))


if __name__ == "__main__":
    unittest.main()
