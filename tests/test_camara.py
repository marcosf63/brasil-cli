"""Testes para o provider Câmara dos Deputados."""

import pytest
import respx
import httpx

from brasil_cli.providers.camara import buscar_deputados, buscar_proposicoes, despesas_deputado, BASE


@pytest.mark.asyncio
async def test_buscar_deputados():
    mock_data = {
        "dados": [
            {"id": 1, "nome": "Fulano", "siglaPartido": "PT", "siglaUf": "CE"},
        ]
    }

    with respx.mock:
        respx.get(f"{BASE}/deputados").mock(
            return_value=httpx.Response(200, json=mock_data)
        )
        result = await buscar_deputados(nome="Fulano")

    assert len(result["dados"]) == 1
    assert result["dados"][0]["siglaUf"] == "CE"


@pytest.mark.asyncio
async def test_buscar_proposicoes():
    mock_data = {
        "dados": [
            {"id": 100, "siglaTipo": "PL", "numero": 1234, "ano": 2024, "ementa": "Teste"},
        ]
    }

    with respx.mock:
        respx.get(f"{BASE}/proposicoes").mock(
            return_value=httpx.Response(200, json=mock_data)
        )
        result = await buscar_proposicoes(keywords="teste", ano=2024)

    assert result["dados"][0]["siglaTipo"] == "PL"


@pytest.mark.asyncio
async def test_despesas_deputado():
    mock_data = {
        "dados": [
            {
                "dataDocumento": "2024-03-15",
                "tipoDespesa": "COMBUSTÍVEIS",
                "nomeFornecedor": "Posto XYZ",
                "valorDocumento": 250.50,
            },
        ]
    }

    with respx.mock:
        respx.get(f"{BASE}/deputados/12345/despesas").mock(
            return_value=httpx.Response(200, json=mock_data)
        )
        result = await despesas_deputado(12345, ano=2024)

    assert len(result["dados"]) == 1
    assert result["dados"][0]["valorDocumento"] == 250.50
