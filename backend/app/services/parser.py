"""Turns the model's JSON-lines output into structured findings.

The model is asked to emit one JSON object per line. The parser is deliberately tolerant
(code fences, prose lines, partial chunks) because LLM output is untrusted input.
"""

import json
from dataclasses import asdict, dataclass

SEVERITIES = ("critical", "high", "medium", "low", "info")
_ALIASES = {"error": "high", "warning": "medium", "warn": "medium", "minor": "low", "note": "info"}


@dataclass(frozen=True)
class ParsedFinding:
    severity: str
    line: int | None
    title: str
    suggestion: str

    def to_dict(self) -> dict:
        return asdict(self)


def parse_summary_line(raw: str) -> str | None:
    text = raw.strip()
    if not (text.startswith("{") and text.endswith("}")):
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if isinstance(data, dict) and isinstance(data.get("summary"), str) and "title" not in data:
        return data["summary"].strip()[:1000]
    return None


def parse_finding_line(raw: str) -> ParsedFinding | None:
    text = raw.strip().rstrip(",")
    if not text.startswith("{") or not text.endswith("}"):
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    title = str(data.get("title", "")).strip()
    if not title:
        return None
    severity = str(data.get("severity", "info")).strip().lower()
    severity = _ALIASES.get(severity, severity)
    if severity not in SEVERITIES:
        severity = "info"
    line = data.get("line")
    try:
        line = None if line is None or isinstance(line, bool) else int(line)
    except (TypeError, ValueError):
        line = None
    if line is not None and line < 1:
        line = None
    return ParsedFinding(
        severity=severity,
        line=line,
        title=title[:300],
        suggestion=str(data.get("suggestion", "")).strip()[:2000],
    )


class FindingStreamParser:
    """Feed arbitrary text chunks; get findings back as soon as a full line is available."""

    def __init__(self) -> None:
        self._buffer = ""
        self.summary: str | None = None

    def _parse(self, lines: list[str]) -> list[ParsedFinding]:
        out = []
        for line in lines:
            finding = parse_finding_line(line)
            if finding:
                out.append(finding)
            else:
                summary = parse_summary_line(line)
                if summary:
                    self.summary = summary
        return out

    def feed(self, chunk: str) -> list[ParsedFinding]:
        self._buffer += chunk
        *lines, self._buffer = self._buffer.split("\n")
        return self._parse(lines)

    def flush(self) -> list[ParsedFinding]:
        rest, self._buffer = self._buffer, ""
        return self._parse([rest])


def dedupe(findings: list[ParsedFinding]) -> list[ParsedFinding]:
    """Local, deterministic dedupe: same line + same normalized title."""
    seen: set[tuple[int | None, str]] = set()
    out: list[ParsedFinding] = []
    for f in findings:
        key = (f.line, " ".join(f.title.lower().split()))
        if key not in seen:
            seen.add(key)
            out.append(f)
    return out


def sort_findings(findings: list[ParsedFinding]) -> list[ParsedFinding]:
    order = {s: i for i, s in enumerate(SEVERITIES)}
    return sorted(findings, key=lambda f: (order[f.severity], f.line or 10**9))
