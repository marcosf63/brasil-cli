"""Testes para o HTTP client compartilhado."""

import pytest
import respx
import httpx

from brasil_cli.http_client import fetch_json


@pytest.mark.asyncio
async def test_fetch_json_success():
    with respx.mock:
        respx.get("https://example.com/api").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        result = await fetch_json("https://example.com/api")

    assert result == {"ok": True}


@pytest.mark.asyncio
async def test_fetch_json_with_params():
    with respx.mock:
        respx.get("https://example.com/api").mock(
            return_value=httpx.Response(200, json=[1, 2, 3])
        )
        result = await fetch_json("https://example.com/api", params={"q": "test"})

    assert result == [1, 2, 3]


@pytest.mark.asyncio
async def test_fetch_json_retries_then_succeeds():
    with respx.mock:
        route = respx.get("https://example.com/flaky")
        route.side_effect = [
            httpx.Response(503),
            httpx.Response(200, json={"recovered": True}),
        ]
        result = await fetch_json("https://example.com/flaky", retries=3)

    assert result["recovered"] is True


@pytest.mark.asyncio
async def test_fetch_json_all_retries_fail():
    with respx.mock:
        respx.get("https://example.com/down").mock(
            return_value=httpx.Response(500)
        )
        with pytest.raises(ConnectionError, match="Falha após"):
            await fetch_json("https://example.com/down", retries=2)
