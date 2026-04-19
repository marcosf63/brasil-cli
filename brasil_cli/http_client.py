"""Shared async HTTP client with retry and rate limiting."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

DEFAULT_TIMEOUT = 30.0
MAX_RETRIES = 3
BACKOFF_FACTOR = 1.5


async def fetch_json(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    retries: int = MAX_RETRIES,
) -> Any:
    """GET request with exponential backoff retry."""
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(url, params=params, headers=headers)
                resp.raise_for_status()
                return resp.json()
        except (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException) as exc:
            last_exc = exc
            if attempt < retries - 1:
                wait = BACKOFF_FACTOR ** attempt
                await asyncio.sleep(wait)
    raise ConnectionError(f"Falha após {retries} tentativas: {last_exc}")
