"""Gateway-level protections. Everything here is enforced server-side, before any LLM call."""

import time
from collections import defaultdict, deque

from fastapi import HTTPException


class RateLimiter:
    """Sliding-window limiter, per key, in memory (single process; see README for Redis)."""

    def __init__(self, max_calls: int, window_seconds: float = 60.0) -> None:
        self.max_calls = max_calls
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        hits = self._hits[key]
        while hits and hits[0] <= now - self.window:
            hits.popleft()
        if len(hits) >= self.max_calls:
            retry = max(int(self.window - (now - hits[0])) + 1, 1)
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Slow down and retry shortly.",
                headers={"Retry-After": str(retry)},
            )
        hits.append(now)


def enforce_quota(used: int, limit: int, plan_id: str) -> None:
    if used >= limit:
        raise HTTPException(
            status_code=402,
            detail=f"Monthly review limit reached for the {plan_id} plan ({used}/{limit}). "
            "Upgrade to continue.",
        )


def enforce_size(code: str, max_chars: int) -> None:
    if len(code) > max_chars:
        raise HTTPException(
            status_code=413, detail=f"Input too large: {len(code)} chars (max {max_chars})."
        )
