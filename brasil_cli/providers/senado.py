"""Senado Federal — senadores, matérias, votações, comissões."""

from __future__ import annotations

from brasil_cli.http_client import fetch_json

BASE = "https://legis.senado.leg.br/dadosabertos"


async def listar_senadores() -> list[dict]:
    """Lista senadores em exercício."""
    resp = await fetch_json(f"{BASE}/senador/lista/atual.json")
    return (
        resp.get("ListaParlamentarEmExercicio", {})
        .get("Parlamentares", {})
        .get("Parlamentar", [])
    )


async def detalhes_senador(codigo: str) -> dict:
    """Detalhes de um senador pelo código."""
    resp = await fetch_json(f"{BASE}/senador/{codigo}.json")
    return resp.get("DetalheParlamentar", {}).get("Parlamentar", {})


async def buscar_materias(
    sigla_tipo: str | None = None,
    numero: str | None = None,
    ano: int | None = None,
    keywords: str | None = None,
    pagina: int = 1,
) -> list[dict]:
    """Busca matérias legislativas no Senado."""
    params: dict = {"v": "5"}
    if sigla_tipo:
        params["sigla"] = sigla_tipo
    if numero:
        params["numero"] = numero
    if ano:
        params["ano"] = str(ano)
    if keywords:
        params["ementa"] = keywords
    resp = await fetch_json(f"{BASE}/materia/pesquisa/lista.json", params=params)
    return (
        resp.get("PesquisaBasicaMateria", {})
        .get("Materias", {})
        .get("Materia", [])
    )


async def listar_votacoes(ano: str) -> list[dict]:
    """Lista votações plenárias de um ano."""
    resp = await fetch_json(f"{BASE}/plenario/lista/votacao/{ano}.json")
    return (
        resp.get("ListaVotacoes", {})
        .get("Votacoes", {})
        .get("Votacao", [])
    )


async def listar_comissoes() -> list[dict]:
    """Lista comissões atuais do Senado."""
    resp = await fetch_json(f"{BASE}/comissao/lista/atual.json")
    return (
        resp.get("ListaComissoes", {})
        .get("Comissoes", {})
        .get("Comissao", [])
    )
