"""Câmara dos Deputados — proposições, deputados, votações."""

from __future__ import annotations

from brasil_cli.http_client import fetch_json

BASE = "https://dadosabertos.camara.leg.br/api/v2"


async def buscar_deputados(
    nome: str | None = None,
    sigla_uf: str | None = None,
    sigla_partido: str | None = None,
    legislatura: int | None = None,
    pagina: int = 1,
    itens: int = 15,
) -> dict:
    """Busca deputados em exercício."""
    params: dict = {"pagina": pagina, "itens": itens, "ordem": "ASC", "ordenarPor": "nome"}
    if nome:
        params["nome"] = nome
    if sigla_uf:
        params["siglaUf"] = sigla_uf
    if sigla_partido:
        params["siglaPartido"] = sigla_partido
    if legislatura:
        params["idLegislatura"] = legislatura
    return await fetch_json(f"{BASE}/deputados", params=params)


async def detalhes_deputado(id_deputado: int) -> dict:
    """Detalhes de um deputado por ID."""
    return await fetch_json(f"{BASE}/deputados/{id_deputado}")


async def buscar_proposicoes(
    sigla_tipo: str | None = None,
    keywords: str | None = None,
    ano: int | None = None,
    autor: str | None = None,
    pagina: int = 1,
    itens: int = 15,
) -> dict:
    """Busca proposições legislativas."""
    params: dict = {"pagina": pagina, "itens": itens, "ordem": "DESC", "ordenarPor": "id"}
    if sigla_tipo:
        params["siglaTipo"] = sigla_tipo
    if keywords:
        params["keywords"] = keywords
    if ano:
        params["ano"] = ano
    if autor:
        params["autor"] = autor
    return await fetch_json(f"{BASE}/proposicoes", params=params)


async def votacoes_proposicao(id_proposicao: int) -> dict:
    """Votações de uma proposição."""
    return await fetch_json(f"{BASE}/proposicoes/{id_proposicao}/votacoes")


async def despesas_deputado(id_deputado: int, ano: int | None = None, mes: int | None = None) -> dict:
    """Despesas de um deputado (cota parlamentar)."""
    params: dict = {"itens": 30, "ordem": "DESC", "ordenarPor": "dataDocumento"}
    if ano:
        params["ano"] = ano
    if mes:
        params["mes"] = mes
    return await fetch_json(f"{BASE}/deputados/{id_deputado}/despesas", params=params)
