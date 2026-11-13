"""AI agent service: runs the review, then calls itself again to verify and dedupe.

Pass 1 ("review") streams draft findings. Pass 2 ("verify") receives the code plus the drafts and
returns the final list. If pass 2 fails or returns nothing parseable, the locally deduped drafts
are used, so a flaky verifier never loses a review.
"""

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

from app.llm.base import LLMProvider, ProviderError
from app.llm.prompts import (
    REVIEW_SYSTEM,
    VERIFY_SYSTEM,
    review_user_message,
    verify_user_message,
)
from app.services.parser import FindingStreamParser, ParsedFinding, dedupe, sort_findings


@dataclass
class AgentEvent:
    type: str  # token | draft | pass | final
    data: dict = field(default_factory=dict)


async def run_review(provider: LLMProvider, code: str, language: str) -> AsyncIterator[AgentEvent]:
    # Pass 1: review
    parser = FindingStreamParser()
    drafts: list[ParsedFinding] = []
    yield AgentEvent("pass", {"name": "review"})
    async for chunk in provider.stream(
        system=REVIEW_SYSTEM, user=review_user_message(code, language), purpose="review"
    ):
        yield AgentEvent("token", {"text": chunk})
        for finding in parser.feed(chunk):
            drafts.append(finding)
            yield AgentEvent("draft", finding.to_dict())
    for finding in parser.flush():
        drafts.append(finding)
        yield AgentEvent("draft", finding.to_dict())

    # Pass 2: the agent calls itself again to verify and dedupe its own draft.
    final = dedupe(drafts)
    summary = f"{len(final)} finding(s)."
    if len(drafts) > 1:
        yield AgentEvent("pass", {"name": "verify"})
        verifier = FindingStreamParser()
        verified: list[ParsedFinding] = []
        drafts_jsonl = "\n".join(json.dumps(d.to_dict()) for d in drafts)
        try:
            async for chunk in provider.stream(
                system=VERIFY_SYSTEM,
                user=verify_user_message(code, language, drafts_jsonl),
                purpose="verify",
            ):
                verified.extend(verifier.feed(chunk))
            verified.extend(verifier.flush())
        except ProviderError:
            verified = []
        if verified:
            final = dedupe(verified)
            summary = verifier.summary or f"{len(final)} finding(s) after verification."
    yield AgentEvent(
        "final", {"findings": [f.to_dict() for f in sort_findings(final)], "summary": summary}
    )
