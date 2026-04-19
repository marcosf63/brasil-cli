"""Testes para o provider IBGE."""

import pytest
import respx
import httpx

from brasil_cli.providers.ibge import listar_estados, listar_municipios, ranking_nomes, BASE


@pytest.mark.asyncio
async def test_listar_estados():
    mock_data = [
        {"id": 23, "sigla": "CE", "nome": "Ceará"},
        {"id": 35, "sigla": "SP", "nome": "São Paulo"},
    ]

    with respx.mock:
        respx.get(f"{BASE}/localidades/estados").mock(
            return_value=httpx.Response(200, json=mock_data)
        )
        result = await listar_estados()

    assert len(result) == 2
    assert result[0]["sigla"] == "CE"


@pytest.mark.asyncio
async def test_listar_municipios():
    mock_data = [
        {"id": 2312908, "nome": "Sobral"},
        {"id": 2304400, "nome": "Fortaleza"},
    ]

    with respx.mock:
        respx.get(f"{BASE}/localidades/estados/CE/municipios").mock(
            return_value=httpx.Response(200, json=mock_data)
        )
        result = await listar_municipios("CE")

    assert len(result) == 2
    assert result[0]["nome"] == "Sobral"


@pytest.mark.asyncio
async def test_ranking_nomes():
    mock_data = [
        {
            "nome": "MARCOS",
            "sexo": None,
            "localidade": "BR",
            "res": [
                {"periodo": "[1930,1940[", "frequencia": 5765},
                {"periodo": "[1940,1950[", "frequencia": 23436},
            ],
        }
    ]

    with respx.mock:
        respx.get("https://servicodados.ibge.gov.br/api/v2/censos/nomes/marcos").mock(
            return_value=httpx.Response(200, json=mock_data)
        )
        result = await ranking_nomes("marcos")

    assert result[0]["nome"] == "MARCOS"
    assert len(result[0]["res"]) == 2
