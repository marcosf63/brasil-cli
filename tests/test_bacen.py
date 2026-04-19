"""Testes para o provider Bacen."""

import pytest
import respx
import httpx

from brasil_cli.providers.bacen import consultar_serie, buscar_serie, indicadores_atuais, expectativas_focus, SERIES, BASE


@pytest.mark.asyncio
async def test_consultar_serie_ultimos():
    codigo = 432
    url = f"{BASE}.{codigo}/dados/ultimos/5"
    mock_data = [
        {"data": "01/2025", "valor": "13.25"},
        {"data": "02/2025", "valor": "13.25"},
    ]

    with respx.mock:
        respx.get(url).mock(return_value=httpx.Response(200, json=mock_data))
        result = await consultar_serie(codigo, ultimos=5)

    assert len(result) == 2
    assert result[0]["valor"] == "13.25"


@pytest.mark.asyncio
async def test_consultar_serie_por_periodo():
    codigo = 433
    url = f"{BASE}.{codigo}/dados"
    mock_data = [{"data": "01/01/2024", "valor": "0.56"}]

    with respx.mock:
        respx.get(url).mock(return_value=httpx.Response(200, json=mock_data))
        result = await consultar_serie(codigo, data_inicial="01/01/2024", data_final="31/01/2024")

    assert len(result) == 1


@pytest.mark.asyncio
async def test_consultar_serie_retry_on_failure():
    codigo = 11
    url = f"{BASE}.{codigo}/dados/ultimos/1"

    with respx.mock:
        route = respx.get(url)
        route.side_effect = [
            httpx.Response(500),
            httpx.Response(200, json=[{"data": "01/2025", "valor": "0.04"}]),
        ]
        result = await consultar_serie(codigo, ultimos=1)

    assert result[0]["valor"] == "0.04"


def test_series_catalog():
    assert "selic" in SERIES
    assert "ipca" in SERIES
    assert "cambio_venda" in SERIES
    assert "cdi" in SERIES
    assert isinstance(SERIES["selic"], int)


@pytest.mark.asyncio
async def test_buscar_serie_encontra():
    result = await buscar_serie("pib")
    assert "pib_mensal" in result
    assert isinstance(result["pib_mensal"], int)


@pytest.mark.asyncio
async def test_buscar_serie_vazio():
    result = await buscar_serie("xyzinexistente")
    assert result == {}


@pytest.mark.asyncio
async def test_indicadores_atuais():
    codigo_selic = SERIES["selic"]
    url_selic = f"{BASE}.{codigo_selic}/dados/ultimos/1"
    codigo_ipca = SERIES["ipca"]
    url_ipca = f"{BASE}.{codigo_ipca}/dados/ultimos/1"
    codigo_cambio = SERIES["cambio_venda"]
    url_cambio = f"{BASE}.{codigo_cambio}/dados/ultimos/1"
    codigo_cdi = SERIES["cdi"]
    url_cdi = f"{BASE}.{codigo_cdi}/dados/ultimos/1"
    codigo_desemprego = SERIES["desemprego"]
    url_desemprego = f"{BASE}.{codigo_desemprego}/dados/ultimos/1"

    with respx.mock:
        respx.get(url_selic).mock(return_value=httpx.Response(200, json=[{"data": "04/2026", "valor": "13.75"}]))
        respx.get(url_ipca).mock(return_value=httpx.Response(200, json=[{"data": "03/2026", "valor": "0.56"}]))
        respx.get(url_cambio).mock(return_value=httpx.Response(200, json=[{"data": "18/04/2026", "valor": "5.72"}]))
        respx.get(url_cdi).mock(return_value=httpx.Response(200, json=[{"data": "18/04/2026", "valor": "0.0523"}]))
        respx.get(url_desemprego).mock(return_value=httpx.Response(200, json=[{"data": "01/2026", "valor": "6.8"}]))
        result = await indicadores_atuais()

    assert "selic" in result
    assert "ipca" in result
    assert "13.75" in result["selic"]


@pytest.mark.asyncio
async def test_expectativas_focus():
    mock_data = {
        "value": [
            {
                "Indicador": "IPCA",
                "Data": "2026-04-18",
                "DataReferencia": "2026",
                "Media": 4.5,
                "Mediana": 4.4,
                "Minimo": 4.0,
                "Maximo": 5.0,
            }
        ]
    }

    with respx.mock:
        respx.get(
            "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/ExpectativaMercadoAnuais"
        ).mock(return_value=httpx.Response(200, json=mock_data))
        result = await expectativas_focus("IPCA", limite=1)

    assert len(result) == 1
    assert result[0]["Indicador"] == "IPCA"
    assert result[0]["Media"] == 4.5
