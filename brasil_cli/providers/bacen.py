"""Banco Central do Brasil — séries temporais via SGS."""

from __future__ import annotations

from brasil_cli.http_client import fetch_json

BASE = "https://api.bcb.gov.br/dados/serie/bcdata.sgs"

# Códigos SGS mais utilizados
SERIES = {
    "selic": 432,         # Selic meta (% a.a.)
    "selic_diaria": 11,   # Selic diária
    "ipca": 433,          # IPCA mensal
    "igpm": 189,          # IGP-M mensal
    "inpc": 188,          # INPC mensal
    "cambio_compra": 10813,  # Dólar PTAX compra
    "cambio_venda": 1,       # Dólar PTAX venda
    "cdi": 12,            # CDI diário
    "pib_mensal": 4380,   # PIB mensal
    "divida_liquida_pib": 4513,  # Dívida líquida / PIB
    "desemprego": 24369,  # Taxa de desemprego PNAD
}


async def consultar_serie(
    codigo: int,
    *,
    ultimos: int | None = None,
    data_inicial: str | None = None,
    data_final: str | None = None,
) -> list[dict]:
    """Consulta série SGS do Bacen.

    Args:
        codigo: Código numérico da série SGS.
        ultimos: Retorna os N últimos valores (max 20).
        data_inicial: dd/MM/aaaa
        data_final: dd/MM/aaaa
    """
    if ultimos:
        url = f"{BASE}.{codigo}/dados/ultimos/{min(ultimos, 20)}"
        params = {"formato": "json"}
    else:
        url = f"{BASE}.{codigo}/dados"
        params: dict[str, str] = {"formato": "json"}
        if data_inicial:
            params["dataInicial"] = data_inicial
        if data_final:
            params["dataFinal"] = data_final
    return await fetch_json(url, params=params)


async def listar_series() -> dict[str, int]:
    """Retorna dicionário nome -> código das séries pré-cadastradas."""
    return SERIES


async def buscar_serie(termo: str) -> dict[str, int]:
    """Busca séries pré-cadastradas por nome (busca parcial, case-insensitive)."""
    termo_lower = termo.lower()
    return {nome: codigo for nome, codigo in SERIES.items() if termo_lower in nome.lower()}


async def indicadores_atuais() -> dict[str, str]:
    """Retorna o valor mais recente dos principais indicadores econômicos."""
    indicadores = {
        "selic": SERIES["selic"],
        "ipca": SERIES["ipca"],
        "cambio_venda": SERIES["cambio_venda"],
        "cdi": SERIES["cdi"],
        "desemprego": SERIES["desemprego"],
    }
    resultado: dict[str, str] = {}
    for nome, codigo in indicadores.items():
        try:
            dados = await consultar_serie(codigo, ultimos=1)
            if dados:
                resultado[nome] = f'{dados[-1].get("valor", "N/A")} ({dados[-1].get("data", "")})'
        except Exception:
            resultado[nome] = "indisponível"
    return resultado


async def expectativas_focus(
    indicador: str,
    data_inicio: str | None = None,
    limite: int = 10,
) -> list[dict]:
    """Expectativas de mercado do Boletim Focus (Bacen Olinda API).

    Args:
        indicador: IPCA, IGP-M, Selic, Câmbio, PIB Total
        data_inicio: Data mínima no formato YYYY-MM-DD
        limite: Número máximo de registros
    """
    url = (
        "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata"
        "/ExpectativaMercadoAnuais"
    )
    filtros = [f"Indicador eq '{indicador}'"]
    if data_inicio:
        filtros.append(f"Data ge '{data_inicio}'")
    params = {
        "$filter": " and ".join(filtros),
        "$orderby": "Data desc",
        "$top": str(limite),
        "$format": "json",
        "$select": "Indicador,Data,DataReferencia,Media,Mediana,Minimo,Maximo",
    }
    resp = await fetch_json(url, params=params)
    return resp.get("value", [])
