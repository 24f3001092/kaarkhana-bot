
import asyncio
import logging
from typing import Any

import httpx

from .base import AIProvider
from ..config import SARVAM_API_KEY, SARVAM_BASE_URL, SARVAM_MODEL, SARVAM_TIMEOUT_SECONDS, SARVAM_MAX_RETRIES

log = logging.getLogger("kaarkhanabot.sarvam")

class ProviderError(RuntimeError):
    pass

class SarvamProvider(AIProvider):
    name = "sarvam"

    def __init__(self):
        if not SARVAM_API_KEY:
            raise ProviderError("SARVAM_API_KEY is not configured.")
        self.url = f"{SARVAM_BASE_URL}/v1/chat/completions"

    async def _call(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "api-subscription-key": SARVAM_API_KEY,
            "Content-Type": "application/json",
        }
        last = None
        for attempt in range(SARVAM_MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=SARVAM_TIMEOUT_SECONDS) as client:
                    r = await client.post(self.url, headers=headers, json=payload)
                if r.status_code in (429, 500, 502, 503, 504) and attempt < SARVAM_MAX_RETRIES:
                    await asyncio.sleep(1.5 * (attempt + 1))
                    continue
                if r.status_code >= 400:
                    # Never log the key or the complete request.
                    detail = r.text[:500]
                    raise ProviderError(f"Sarvam API returned HTTP {r.status_code}: {detail}")
                return r.json()
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last = exc
                if attempt < SARVAM_MAX_RETRIES:
                    await asyncio.sleep(1.5 * (attempt + 1))
                    continue
                raise ProviderError("Sarvam API request timed out or could not reach the service.") from exc
        raise ProviderError("Sarvam API request failed.") from last

    async def structured(self, messages, schema, schema_name):
        payload = {
            "model": SARVAM_MODEL,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 1800,
            "reasoning_effort": "low",
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "strict": True,
                    "schema": schema,
                },
            },
        }
        data = await self._call(payload)
        try:
            import json
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)
        except Exception as exc:
            raise ProviderError("Sarvam returned an invalid structured response.") from exc

    async def text(self, messages, *, max_tokens=2500):
        payload = {
            "model": SARVAM_MODEL,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": max_tokens,
            "reasoning_effort": "low",
        }
        data = await self._call(payload)
        try:
            return data["choices"][0]["message"]["content"]
        except Exception as exc:
            raise ProviderError("Sarvam returned an invalid text response.") from exc
