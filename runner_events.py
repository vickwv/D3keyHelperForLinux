"""Protocol for structured events emitted by the runner process on stdout.

The runner prints `EVENT:<kind>[:<data>]` lines followed by human-readable text.
The GUI parses these to drive state updates and beep logic without relying on
language-specific message text.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class RunnerEvent:
    kind: str
    profile: str = ""
    reason: str = ""


_KNOWN_KINDS = frozenset({
    "macro_started",
    "macro_stopped",
    "macro_paused",
    "macro_resumed",
    "profile_switched",
})


def parse_runner_event(line: str) -> RunnerEvent | None:
    """Parse a single stdout line.  Returns None if it is not an EVENT line."""
    line = line.strip()
    if not line.startswith("EVENT:"):
        return None
    rest = line[6:]
    kind, sep, data = rest.partition(":")
    if kind not in _KNOWN_KINDS:
        return None
    event = RunnerEvent(kind=kind)
    if kind in ("macro_started", "profile_switched"):
        event.profile = data
    elif kind == "macro_stopped":
        event.reason = data
    return event
