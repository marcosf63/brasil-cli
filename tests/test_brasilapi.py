"""Testes para o provider BrasilAPI."""

import pytest
import respx
import httpx

from brasil_cli.providers.brasilapi import consultar_cep, consultar_cnpj, feriados, consultar_ddd, BASE


@pytest.mark.asyncio
async def test_consultar_cep():
    mock_data = {
        "cep": "63000000",
        "state": "CE",
        "city": "Juazeiro do Norte",
        "neighborhood": "Centro",
        "street": "",
    }

    with respx.mock:
        respx.get(f"{BASE}/cep/v2/63000000").mock(
            return_value=httpx.Response(200, json=mock_data)
        )
        result = await consultar_cep("63000-000")

    assert result["city"] == "Juazeiro do Norte"
    assert result["state"] == "CE"


@pytest.mark.asyncio
async def test_consultar_cnpj():
    mock_data = {
        "cnpj": "00000000000191",
        "razao_social": "BANCO DO BRASIL SA",
        "nome_fantasia": "BANCO DO BRASIL",
        "capital_social": 120000000000,
        "uf": "DF",
    }

    with respx.mock:
        respx.get(f"{BASE}/cnpj/v1/00000000000191").mock(
            return_value=httpx.Response(200, json=mock_data)
        )
        result = await consultar_cnpj("00.000.000/0001-91")

    assert result["razao_social"] == "BANCO DO BRASIL SA"


@pytest.mark.asyncio
async def test_feriados():
    mock_data = [
        {"date": "2026-01-01", "name": "Confraternização Universal", "type": "national"},
        {"date": "2026-04-21", "name": "Tiradentes", "type": "national"},
    ]

    with respx.mock:
        respx.get(f"{BASE}/feriados/v1/2026").mock(
            return_value=httpx.Response(200, json=mock_data)
        )
        result = await feriados(2026)

    assert len(result) == 2
    assert result[0]["name"] == "Confraternização Universal"


@pytest.mark.asyncio
async def test_consultar_ddd():
    mock_data = {
        "state": "CE",
        "cities": ["JUAZEIRO DO NORTE", "CRATO", "BARBALHA"],
    }

    with respx.mock:
        respx.get(f"{BASE}/ddd/v1/88").mock(
            return_value=httpx.Response(200, json=mock_data)
        )
        result = await consultar_ddd(88)

    assert result["state"] == "CE"
    assert "JUAZEIRO DO NORTE" in result["cities"]
