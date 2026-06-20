# OpenRouter provider — HTTP client for OpenRouter API
from __future__ import annotations

import asyncio
import logging
import time

import httpx

from backend.app.platform.ai.exceptions import ProviderError

logger = logging.getLogger(__name__)


class OpenRouterProvider:

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout: int,
        max_retries: int,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._max_retries = max_retries
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

    @property
    def model(self) -> str:
        return self._model

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict:
        payload: dict = {
            "model": model or self._model,
            "messages": messages,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        url = f"{self._base_url}/chat/completions"
        last_error: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:

                response = await self._client.post(url, json=payload)
                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as exc:
                last_error = exc
                status = exc.response.status_code

                if status < 500 and status != 429:
                    break

                if attempt < self._max_retries:
                    await asyncio.sleep(2**attempt)

            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = exc

                if attempt < self._max_retries:
                    await asyncio.sleep(2**attempt)

        raise ProviderError(
            f"OpenRouter request failed after {self._max_retries} attempts: {last_error}"
        )

    async def health_check(self) -> bool:
        try:
            response = await self._client.get(f"{self._base_url}/models")
            return response.status_code == 200
        except Exception as exc:
            logger.warning("OpenRouter health check failed: %s", exc)
            return False

    async def close(self) -> None:
        await self._client.aclose()
