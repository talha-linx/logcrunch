"""
Parsing for Apache-style error logs, e.g.:

    [Sun Dec 04 04:47:44 2005] [notice] workerEnv.init() ok /etc/httpd/conf/workers2.properties
    [Sun Dec 04 16:41:22 2005] [error] mod_jk child workerEnv in error state 6

This is the real format used by the Apache HTTP Server's error log
(https://httpd.apache.org/docs/2.4/logs.html#errorlog), also used as a
sample dataset in the loghub system-log research collection
(https://github.com/logpai/loghub).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

LOG_LINE_RE = re.compile(
    r"^\[(?P<timestamp>[A-Za-z]{3} [A-Za-z]{3} \d{2} \d{2}:\d{2}:\d{2} \d{4})\]"
    r"\s*\[(?P<level>[a-zA-Z]+)\]\s*(?P<message>.*)$"
)

TIMESTAMP_FORMAT = "%a %b %d %H:%M:%S %Y"


@dataclass(frozen=True)
class LogRecord:
    timestamp: datetime
    level: str
    message: str
    raw: str


class ParseError(ValueError):
    """Raised when a line doesn't match the expected log format."""


def parse_line(line: str) -> Optional[LogRecord]:
    """Parse one log line into a LogRecord, or return None for a blank line.

    Raises ParseError on a non-blank line that doesn't match the expected
    format, so callers can decide whether to skip or fail on malformed
    input (the CLI skips and counts them; tests check both paths).
    """
    line = line.rstrip("\n")
    if not line.strip():
        return None
    match = LOG_LINE_RE.match(line)
    if match is None:
        raise ParseError(f"line did not match expected log format: {line!r}")
    timestamp = datetime.strptime(match.group("timestamp"), TIMESTAMP_FORMAT)
    level = match.group("level").lower()
    message = match.group("message").strip()
    return LogRecord(timestamp=timestamp, level=level, message=message, raw=line)


def parse_lines(lines):
    """Parse an iterable of lines, yielding LogRecords and skipping blanks.

    Malformed lines raise ParseError up to the caller - this function does
    not swallow errors silently.
    """
    for line in lines:
        record = parse_line(line)
        if record is not None:
            yield record
