"""Protocol for structured events emitted by the runner process on stdout.

The runner prints `EVENT:<kind>[:<data>]` lines followed by human-readable text.
The GUI parses these to drive state updates and beep logic without relying on
language-specific message text.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import TextIO
import sys


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


def format_runner_event(kind: str, data: str = "") -> str:
    """Return the stdout protocol line for a structured runner event."""
    if kind not in _KNOWN_KINDS:
        raise ValueError(f"Unknown runner event kind: {kind}")
    suffix = f":{data}" if data else ""
    return f"EVENT:{kind}{suffix}"


def emit_runner_event(kind: str, data: str = "", stream: TextIO | None = None) -> None:
    """Print a structured runner event line and flush immediately."""
    print(format_runner_event(kind, data), file=stream or sys.stdout, flush=True)


def emit_runner_log(message: str, stream: TextIO | None = None) -> None:
    """Print a human-readable runner log line and flush immediately."""
    print(message, file=stream or sys.stdout, flush=True)


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
