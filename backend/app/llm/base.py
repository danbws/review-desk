from collections.abc import AsyncIterator
from typing import Protocol


class ProviderError(Exception):
    """Raised when the LLM provider fails or refuses; the message is safe to show users."""


class LLMProvider(Protocol):
    name: str

    def stream(self, *, system: str, user: str, purpose: str) -> AsyncIterator[str]:
        """Yield text chunks. `purpose` is "review" or "verify" (keeps the fake deterministic)."""
        ...
