"""Testes para o provider Senado."""

import pytest
import respx
import httpx

from brasil_cli.providers.senado import (
    listar_senadores,
    detalhes_senador,
    buscar_materias,
    listar_votacoes,
    listar_comissoes,
    BASE,
)


@pytest.mark.asyncio
async def test_listar_senadores():
    mock_data = {
        "ListaParlamentarEmExercicio": {
            "Parlamentares": {
                "Parlamentar": [
                    {
                        "IdentificacaoParlamentar": {
                            "CodigoParlamentar": "5529",
                            "NomeParlamentar": "Rodrigo Pacheco",
                            "SiglaPartidoParlamentar": "PSD",
                            "UfParlamentar": "MG",
                        }
                    }
                ]
            }
        }
    }

    with respx.mock:
        respx.get(f"{BASE}/senador/lista/atual.json").mock(
            return_value=httpx.Response(200, json=mock_data)
        )
        result = await listar_senadores()

    assert len(result) == 1
    assert result[0]["IdentificacaoParlamentar"]["NomeParlamentar"] == "Rodrigo Pacheco"
    assert result[0]["IdentificacaoParlamentar"]["UfParlamentar"] == "MG"


@pytest.mark.asyncio
async def test_detalhes_senador():
    mock_data = {
        "DetalheParlamentar": {
            "Parlamentar": {
                "IdentificacaoParlamentar": {
                    "CodigoParlamentar": "5529",
                    "NomeParlamentar": "Rodrigo Pacheco",
                    "SiglaPartidoParlamentar": "PSD",
                    "UfParlamentar": "MG",
                    "EmailParlamentar": "sen.rodrigopacheco@senado.leg.br",
                }
            }
        }
    }

    with respx.mock:
        respx.get(f"{BASE}/senador/5529.json").mock(
            return_value=httpx.Response(200, json=mock_data)
        )
        result = await detalhes_senador("5529")

    assert result["IdentificacaoParlamentar"]["NomeParlamentar"] == "Rodrigo Pacheco"


@pytest.mark.asyncio
async def test_buscar_materias():
    mock_data = {
        "PesquisaBasicaMateria": {
            "Materias": {
                "Materia": [
                    {
                        "CodigoMateria": "123",
                        "SiglaSubtipoMateria": "PEC",
                        "NumeroMateria": "45",
                        "AnoMateria": "2023",
                        "EmentaMateria": "Altera a Constituição Federal",
                    }
                ]
            }
        }
    }

    with respx.mock:
        respx.get(f"{BASE}/materia/pesquisa/lista.json").mock(
            return_value=httpx.Response(200, json=mock_data)
        )
        result = await buscar_materias(sigla_tipo="PEC", ano=2023)

    assert len(result) == 1
    assert result[0]["CodigoMateria"] == "123"


@pytest.mark.asyncio
async def test_listar_votacoes():
    mock_data = {
        "ListaVotacoes": {
            "Votacoes": {
                "Votacao": [
                    {
                        "CodigoSessaoVotacao": "9001",
                        "DataSessao": "2024-03-15",
                        "DescricaoVotacao": "PEC 45/2023",
                        "DescricaoResultado": "Aprovado",
                    }
                ]
            }
        }
    }

    with respx.mock:
        respx.get(f"{BASE}/plenario/lista/votacao/2024.json").mock(
            return_value=httpx.Response(200, json=mock_data)
        )
        result = await listar_votacoes("2024")

    assert len(result) == 1
    assert result[0]["DescricaoResultado"] == "Aprovado"


@pytest.mark.asyncio
async def test_listar_comissoes():
    mock_data = {
        "ListaComissoes": {
            "Comissoes": {
                "Comissao": [
                    {
                        "CodigoComissao": "10",
                        "SiglaComissao": "CCJ",
                        "NomeComissao": "Comissão de Constituição, Justiça e Cidadania",
                        "TipoComissao": "Permanente",
                    }
                ]
            }
        }
    }

    with respx.mock:
        respx.get(f"{BASE}/comissao/lista/atual.json").mock(
            return_value=httpx.Response(200, json=mock_data)
        )
        result = await listar_comissoes()

    assert len(result) == 1
    assert result[0]["SiglaComissao"] == "CCJ"
