from collections.abc import AsyncIterator

import anthropic

from app.llm.base import ProviderError


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str, model: str = "claude-sonnet-5-5") -> None:
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model

    async def stream(self, *, system: str, user: str, purpose: str) -> AsyncIterator[str]:
        try:
            # Beta endpoint only for the server-side refusal fallback: if the safety classifier
            # declines, the API routes the request to a fallback model instead of failing.
            async with self._client.beta.messages.stream(
                model=self._model,
                max_tokens=8000,
                system=system,
                messages=[{"role": "user", "content": user}],
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            ) as stream:
                async for text in stream.text_stream:
                    yield text
                final = await stream.get_final_message()
            if final.stop_reason == "refusal":
                raise ProviderError("The model declined to review this input.")
        except anthropic.RateLimitError as exc:
            raise ProviderError("The AI provider is rate limiting us; try again shortly.") from exc
        except anthropic.APIConnectionError as exc:
            raise ProviderError("Could not reach the AI provider.") from exc
        except anthropic.APIStatusError as exc:
            raise ProviderError(f"AI provider error (HTTP {exc.status_code}).") from exc
