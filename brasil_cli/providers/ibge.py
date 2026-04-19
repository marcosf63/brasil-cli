"""IBGE — localidades, população, indicadores e nomes."""

from __future__ import annotations

from brasil_cli.http_client import fetch_json

BASE = "https://servicodados.ibge.gov.br/api/v1"
BASE_V3 = "https://servicodados.ibge.gov.br/api/v3"


async def listar_estados() -> list[dict]:
    """Lista todos os estados brasileiros."""
    return await fetch_json(f"{BASE}/localidades/estados", params={"orderBy": "nome"})


async def listar_municipios(uf: str) -> list[dict]:
    """Lista municípios de um estado (sigla UF)."""
    return await fetch_json(f"{BASE}/localidades/estados/{uf}/municipios", params={"orderBy": "nome"})


async def buscar_municipio(nome: str) -> list[dict]:
    """Busca municípios por nome."""
    todos = await fetch_json(f"{BASE}/localidades/municipios", params={"orderBy": "nome"})
    nome_lower = nome.lower()
    return [m for m in todos if nome_lower in m.get("nome", "").lower()]


async def populacao_estimada(localidade: str = "BR") -> list[dict]:
    """População estimada — agregado IBGE (tabela 6579)."""
    url = f"{BASE_V3}/agregados/6579/periodos/-1/variaveis/9324"
    params = {"localidades": f"N1[{localidade}]"}
    return await fetch_json(url, params=params)


async def ranking_nomes(nome: str) -> list[dict]:
    """Ranking de frequência de um nome no Brasil."""
    url = f"https://servicodados.ibge.gov.br/api/v2/censos/nomes/{nome}"
    return await fetch_json(url)


async def indicadores_pib() -> list[dict]:
    """PIB trimestral — variação % (agregado 5932)."""
    url = f"{BASE_V3}/agregados/5932/periodos/-6/variaveis/6564"
    params = {"localidades": "N1[all]"}
    return await fetch_json(url, params=params)
