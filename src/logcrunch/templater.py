"""
Crude message "templating": collapse variable tokens (numbers, hex IDs) in
a log message so that repeated event types group together even when they
carry different IDs, e.g.:

    "jk2_init() Found child 32710 in scoreboard slot 9"
    "jk2_init() Found child  5998 in scoreboard slot 6"

both become the template:

    "jk2_init() Found child <NUM> in scoreboard slot <NUM>"

This is a simplified version of the log-template-mining idea used by real
tools like Drain (https://github.com/logpai/Drain3) - good enough to spot
"the same kind of event happened N times" without a full parser per message
type, which would be overkill for this log format's small vocabulary.
"""
import re

_NUMBER_RE = re.compile(r"\b\d+\b")
_HEX_RE = re.compile(r"\b0x[0-9a-fA-F]+\b")


def to_template(message: str) -> str:
    template = _HEX_RE.sub("<HEX>", message)
    template = _NUMBER_RE.sub("<NUM>", template)
    return template
