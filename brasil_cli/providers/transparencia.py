"""Portal da Transparência — contratos, servidores, despesas."""

from __future__ import annotations

from brasil_cli.http_client import fetch_json

BASE = "https://api.portaldatransparencia.gov.br/api-de-dados"


def _headers(api_key: str) -> dict[str, str]:
    return {"chave-api-dados": api_key, "Accept": "application/json"}


async def buscar_contratos(
    api_key: str,
    data_inicial: str | None = None,
    data_final: str | None = None,
    orgao: str | None = None,
    pagina: int = 1,
) -> list[dict]:
    """Busca contratos do governo federal."""
    params: dict = {"pagina": pagina}
    if data_inicial:
        params["dataInicial"] = data_inicial
    if data_final:
        params["dataFinal"] = data_final
    if orgao:
        params["codigoOrgao"] = orgao
    return await fetch_json(
        f"{BASE}/contratos", params=params, headers=_headers(api_key)
    )


async def buscar_servidores(
    api_key: str,
    nome: str | None = None,
    orgao: str | None = None,
    pagina: int = 1,
) -> list[dict]:
    """Busca servidores federais."""
    params: dict = {"pagina": pagina}
    if nome:
        params["nome"] = nome
    if orgao:
        params["orgaoServidorExercicio"] = orgao
    return await fetch_json(
        f"{BASE}/servidores", params=params, headers=_headers(api_key)
    )


async def buscar_despesas(
    api_key: str,
    ano: int,
    pagina: int = 1,
) -> list[dict]:
    """Busca despesas do governo federal por ano."""
    params: dict = {"ano": ano, "pagina": pagina}
    return await fetch_json(
        f"{BASE}/despesas/recursos-recebidos", params=params, headers=_headers(api_key)
    )


async def buscar_licitacoes(
    api_key: str,
    codigo_orgao: str | None = None,
    data_inicial: str | None = None,
    data_final: str | None = None,
    pagina: int = 1,
) -> list[dict]:
    """Busca licitações do governo federal."""
    params: dict = {"pagina": pagina}
    if codigo_orgao:
        params["codigoOrgao"] = codigo_orgao
    if data_inicial:
        params["dataInicial"] = data_inicial
    if data_final:
        params["dataFinal"] = data_final
    return await fetch_json(
        f"{BASE}/licitacoes", params=params, headers=_headers(api_key)
    )


async def buscar_emendas(
    api_key: str,
    ano: int | None = None,
    nome_autor: str | None = None,
    pagina: int = 1,
) -> list[dict]:
    """Busca emendas parlamentares."""
    params: dict = {"pagina": pagina}
    if ano:
        params["ano"] = str(ano)
    if nome_autor:
        params["nomeAutor"] = nome_autor
    return await fetch_json(
        f"{BASE}/emendas", params=params, headers=_headers(api_key)
    )


async def consultar_bolsa_familia(
    api_key: str,
    mes_ano: str,
    codigo_ibge: str | None = None,
    pagina: int = 1,
) -> list[dict]:
    """Consulta pagamentos do Bolsa Família por município (mes_ano: MM/AAAA)."""
    params: dict = {"mesAno": mes_ano, "pagina": pagina}
    if codigo_ibge:
        params["codigoIbge"] = codigo_ibge
    return await fetch_json(
        f"{BASE}/bolsa-familia-por-municipio", params=params, headers=_headers(api_key)
    )


async def buscar_viagens(
    api_key: str,
    cpf: str,
    pagina: int = 1,
) -> list[dict]:
    """Busca viagens a serviço de um servidor pelo CPF."""
    params: dict = {"cpf": cpf, "pagina": pagina}
    return await fetch_json(
        f"{BASE}/viagens", params=params, headers=_headers(api_key)
    )


async def buscar_sancoes(
    api_key: str,
    consulta: str,
    pagina: int = 1,
) -> list[dict]:
    """Busca sanções no CEIS (Cadastro de Empresas Inidôneas e Suspensas)."""
    params: dict = {"cnpjCpf": consulta, "pagina": pagina}
    return await fetch_json(
        f"{BASE}/ceis", params=params, headers=_headers(api_key)
    )
