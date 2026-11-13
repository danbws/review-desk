"""Deterministic provider used by tests, CI and demo mode (no API key needed).

It runs a few cheap regex heuristics over the numbered code so the demo output relates to the
pasted input, and always emits one duplicate draft so the verify pass has work to do.
"""

import asyncio
import json
import re
from collections.abc import AsyncIterator

from app.services.parser import FindingStreamParser, dedupe

_RULES = [
    (
        r"\beval\(|\bexec\(",
        "critical",
        "Use of eval/exec on dynamic input",
        "Replace with a safe parser or an explicit dispatch table.",
    ),
    (
        r"(?i)(password|secret|api_?key|token)\s*=\s*['\"][^'\"]+['\"]",
        "high",
        "Hard-coded credential",
        "Read it from an environment variable or a secrets manager.",
    ),
    (
        r"(?i)(select|insert|update|delete)\b.*(\+|%s|f['\"]|\{)",
        "high",
        "SQL built with string concatenation",
        "Use parameterized queries.",
    ),
    (
        r"except\s*:|except Exception\s*:\s*pass|catch\s*\(\w*\)\s*\{\s*\}",
        "medium",
        "Errors are swallowed",
        "Catch specific exceptions and log or re-raise.",
    ),
    (r"\bTODO\b|\bFIXME\b", "low", "Unresolved TODO/FIXME", "Resolve it or link a ticket."),
    (
        r"\bprint\(|console\.log\(",
        "info",
        "Debug output left in code",
        "Use a logger so output can be controlled.",
    ),
]


def _line_items(user: str) -> list[tuple[int, str]]:
    block = re.search(r"<code>\n(.*?)\n</code>", user, re.S)
    items = []
    for raw in (block.group(1) if block else "").splitlines():
        num, _, text = raw.partition(": ")
        if num.isdigit():
            items.append((int(num), text))
    return items


def _drafts(user: str) -> list[dict]:
    out: list[dict] = []
    for num, text in _line_items(user):
        for pattern, severity, title, suggestion in _RULES:
            if re.search(pattern, text):
                out.append(
                    {"severity": severity, "line": num, "title": title, "suggestion": suggestion}
                )
    if not out:
        out.append(
            {
                "severity": "info",
                "line": None,
                "title": "No obvious issues found by the demo heuristics",
                "suggestion": "Configure a real provider for a deeper review.",
            }
        )
    else:
        out.append(dict(out[0]))  # intentional duplicate: gives the verify pass something to do
    return out


class FakeProvider:
    name = "fake"

    def __init__(self, token_delay_ms: int = 0) -> None:
        self._delay = token_delay_ms / 1000

    async def stream(self, *, system: str, user: str, purpose: str) -> AsyncIterator[str]:
        if purpose == "verify":
            draft = re.search(r"<draft_findings>\n(.*?)\n</draft_findings>", user, re.S)
            parser = FindingStreamParser()
            found = parser.feed((draft.group(1) if draft else "") + "\n") + parser.flush()
            final = dedupe(found)
            lines = [json.dumps(f.to_dict()) for f in final]
            lines.append(json.dumps({"summary": f"{len(final)} issue(s) after verification."}))
        else:
            lines = [json.dumps(d) for d in _drafts(user)]
        text = "\n".join(lines) + "\n"
        for i in range(0, len(text), 12):
            if self._delay:
                await asyncio.sleep(self._delay)
            yield text[i : i + 12]
