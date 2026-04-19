"""BrasilAPI — CEP, CNPJ, bancos, feriados, FIPE, PIX."""

from __future__ import annotations

from brasil_cli.http_client import fetch_json

BASE = "https://brasilapi.com.br/api"


async def consultar_cep(cep: str) -> dict:
    """Consulta endereço por CEP."""
    cep_limpo = cep.replace("-", "").replace(".", "").strip()
    return await fetch_json(f"{BASE}/cep/v2/{cep_limpo}")


async def consultar_cnpj(cnpj: str) -> dict:
    """Consulta dados de empresa por CNPJ."""
    cnpj_limpo = cnpj.replace(".", "").replace("/", "").replace("-", "").strip()
    return await fetch_json(f"{BASE}/cnpj/v1/{cnpj_limpo}")


async def listar_bancos() -> list[dict]:
    """Lista todos os bancos registrados no Brasil."""
    return await fetch_json(f"{BASE}/banks/v1")


async def buscar_banco(codigo: int) -> dict:
    """Busca banco por código."""
    return await fetch_json(f"{BASE}/banks/v1/{codigo}")


async def feriados(ano: int) -> list[dict]:
    """Lista feriados nacionais de um ano."""
    return await fetch_json(f"{BASE}/feriados/v1/{ano}")


async def consultar_ddd(ddd: int) -> dict:
    """Lista cidades de um DDD."""
    return await fetch_json(f"{BASE}/ddd/v1/{ddd}")


async def tabela_fipe(codigo_fipe: str) -> list[dict]:
    """Consulta preço de veículo pela tabela FIPE."""
    return await fetch_json(f"{BASE}/fipe/preco/v1/{codigo_fipe}")


async def listar_marcas_fipe(tipo_veiculo: str = "carros") -> list[dict]:
    """Lista marcas da FIPE por tipo (carros, motos, caminhoes)."""
    return await fetch_json(f"{BASE}/fipe/marcas/v1/{tipo_veiculo}")


async def pix_participantes() -> list[dict]:
    """Lista participantes do PIX."""
    return await fetch_json(f"{BASE}/pix/v1/participants")
