"""Testes para o provider Transparência."""

import pytest
import respx
import httpx

from brasil_cli.providers.transparencia import (
    buscar_contratos,
    buscar_servidores,
    buscar_despesas,
    buscar_licitacoes,
    buscar_emendas,
    consultar_bolsa_familia,
    buscar_viagens,
    buscar_sancoes,
    BASE,
)

API_KEY = "test-key"


@pytest.mark.asyncio
async def test_buscar_contratos():
    mock_data = [
        {
            "id": 1,
            "objeto": "Aquisição de material de escritório",
            "fornecedor": {"nome": "Empresa XYZ"},
            "valorInicial": 50000.0,
        }
    ]

    with respx.mock:
        respx.get(f"{BASE}/contratos").mock(return_value=httpx.Response(200, json=mock_data))
        result = await buscar_contratos(API_KEY, data_inicial="01/01/2024")

    assert len(result) == 1
    assert result[0]["id"] == 1


@pytest.mark.asyncio
async def test_buscar_servidores():
    mock_data = [
        {
            "nome": "JOAO DA SILVA",
            "descricaoCargoEfetivo": "Analista",
            "orgaoExercicio": {"nome": "Ministério da Fazenda"},
            "remuneracaoBasicaBruta": 8000.0,
        }
    ]

    with respx.mock:
        respx.get(f"{BASE}/servidores").mock(return_value=httpx.Response(200, json=mock_data))
        result = await buscar_servidores(API_KEY, nome="joao")

    assert len(result) == 1
    assert result[0]["nome"] == "JOAO DA SILVA"


@pytest.mark.asyncio
async def test_buscar_despesas():
    mock_data = [
        {
            "codigoOrgao": "26000",
            "nomeOrgao": "Ministério da Educação",
            "valorDespesa": "1500000000.00",
        }
    ]

    with respx.mock:
        respx.get(f"{BASE}/despesas/recursos-recebidos").mock(
            return_value=httpx.Response(200, json=mock_data)
        )
        result = await buscar_despesas(API_KEY, ano=2024)

    assert len(result) == 1
    assert result[0]["codigoOrgao"] == "26000"


@pytest.mark.asyncio
async def test_buscar_licitacoes():
    mock_data = [
        {
            "id": 101,
            "objeto": "Serviços de TI",
            "modalidade": {"descricao": "Pregão Eletrônico"},
            "valorLicitacao": 200000.0,
        }
    ]

    with respx.mock:
        respx.get(f"{BASE}/licitacoes").mock(return_value=httpx.Response(200, json=mock_data))
        result = await buscar_licitacoes(API_KEY, codigo_orgao="26000")

    assert len(result) == 1
    assert result[0]["id"] == 101


@pytest.mark.asyncio
async def test_buscar_emendas():
    mock_data = [
        {
            "codigoEmenda": "20240001",
            "nomeAutor": "DEP. FULANO DE TAL",
            "localidadeGasto": "Ceará",
            "valorEmpenhado": 1000000.0,
        }
    ]

    with respx.mock:
        respx.get(f"{BASE}/emendas").mock(return_value=httpx.Response(200, json=mock_data))
        result = await buscar_emendas(API_KEY, ano=2024)

    assert len(result) == 1
    assert result[0]["nomeAutor"] == "DEP. FULANO DE TAL"


@pytest.mark.asyncio
async def test_consultar_bolsa_familia():
    mock_data = [
        {
            "municipio": {"nomeIBGE": "FORTALEZA"},
            "quantidade": 150000,
            "valor": 75000000.0,
        }
    ]

    with respx.mock:
        respx.get(f"{BASE}/bolsa-familia-por-municipio").mock(
            return_value=httpx.Response(200, json=mock_data)
        )
        result = await consultar_bolsa_familia(API_KEY, mes_ano="01/2024", codigo_ibge="2304400")

    assert len(result) == 1
    assert result[0]["quantidade"] == 150000


@pytest.mark.asyncio
async def test_buscar_viagens():
    mock_data = [
        {
            "dataPartida": "2024-03-01T00:00:00",
            "destinos": [{"destino": "Brasília"}],
            "motivo": "Reunião ministerial",
            "valorPassagens": 1200.0,
        }
    ]

    with respx.mock:
        respx.get(f"{BASE}/viagens").mock(return_value=httpx.Response(200, json=mock_data))
        result = await buscar_viagens(API_KEY, cpf="12345678901")

    assert len(result) == 1
    assert result[0]["valorPassagens"] == 1200.0


@pytest.mark.asyncio
async def test_buscar_sancoes():
    mock_data = [
        {
            "nomeInfrator": "EMPRESA FRAUDULENTA LTDA",
            "cpfCnpjInfrator": "00000000000191",
            "tipoSancao": {"descricaoResumida": "Suspensa"},
            "dataInicioSancao": "2023-01-01T00:00:00",
            "dataFimSancao": "2025-01-01T00:00:00",
        }
    ]

    with respx.mock:
        respx.get(f"{BASE}/ceis").mock(return_value=httpx.Response(200, json=mock_data))
        result = await buscar_sancoes(API_KEY, consulta="00000000000191")

    assert len(result) == 1
    assert result[0]["nomeInfrator"] == "EMPRESA FRAUDULENTA LTDA"
