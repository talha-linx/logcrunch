"""
logcrunch - a parallel log-analysis CLI tool.

Parses Apache-style error logs, aggregates stats (level counts, hourly
volume, recurring message templates), and detects anomalous error bursts -
using multiprocessing to split large files across worker processes.
"""

__version__ = "0.1.0"
__author__ = "Muhammad Islam"
