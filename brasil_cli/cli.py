"""brasil-cli — CLI para consulta de APIs públicas brasileiras.

Inspirado na arquitetura do mcp-brasil, mas como CLI standalone
usando Typer + httpx + Rich.
"""

from __future__ import annotations

import asyncio
from typing import Optional

import typer

from brasil_cli.output import (
    console,
    print_error,
    print_info,
    print_kv,
    print_list,
    print_series,
    print_table,
    set_json_mode,
)

app = typer.Typer(
    name="brasil",
    help="🇧🇷 CLI para consulta de APIs públicas brasileiras",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


@app.callback()
def _global_options(
    json_output: bool = typer.Option(False, "--json", help="Saída em JSON (ideal para LLMs e scripts)"),
) -> None:
    set_json_mode(json_output)

# ── Sub-apps ──────────────────────────────────────────────────────

bacen_app = typer.Typer(help="Banco Central — séries SGS (Selic, IPCA, câmbio...)")
ibge_app = typer.Typer(help="IBGE — localidades, população, nomes")
camara_app = typer.Typer(help="Câmara dos Deputados — deputados, proposições, despesas")
br_app = typer.Typer(help="BrasilAPI — CEP, CNPJ, bancos, feriados, FIPE")
transparencia_app = typer.Typer(help="Portal da Transparência — contratos, servidores, despesas")
senado_app = typer.Typer(help="Senado Federal — senadores, matérias, votações, comissões")

app.add_typer(bacen_app, name="bacen")
app.add_typer(ibge_app, name="ibge")
app.add_typer(camara_app, name="camara")
app.add_typer(br_app, name="br")
app.add_typer(transparencia_app, name="transparencia")
app.add_typer(senado_app, name="senado")


def _run(coro):
    """Helper to run async from sync Typer commands."""
    return asyncio.run(coro)


def _paginar_todos(fn, *, limite: int = 1000, **kwargs) -> list:
    """Auto-paginação reutilizável para qualquer provider.

    Suporta dois estilos de resposta:
    - Câmara-style: {"dados": [...], "links": [...]} — para quando não há link "next"
    - Transparência-style: [...] — para quando retorna lista vazia ou menor que page_size
    """
    results: list = []
    pagina = 1
    while len(results) < limite:
        resp = _run(fn(**kwargs, pagina=pagina))
        if isinstance(resp, list):
            if not resp:
                break
            results.extend(resp)
            if len(resp) < 15:
                break
        else:
            dados = resp.get("dados", [])
            if not dados:
                break
            results.extend(dados)
            if not any(lnk.get("rel") == "next" for lnk in resp.get("links", [])):
                break
        pagina += 1
    return results


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BACEN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@bacen_app.command("series")
def bacen_listar_series():
    """Lista séries SGS pré-cadastradas com seus códigos."""
    from brasil_cli.providers.bacen import SERIES

    rows = [[nome, str(codigo)] for nome, codigo in sorted(SERIES.items())]
    print_table("Séries SGS disponíveis", ["Nome", "Código"], rows)


@bacen_app.command("consultar")
def bacen_consultar(
    serie: str = typer.Argument(help="Nome da série (ex: selic, ipca) ou código numérico"),
    ultimos: Optional[int] = typer.Option(None, "--ultimos", "-n", help="Últimos N valores (max 20)"),
    inicio: Optional[str] = typer.Option(None, "--inicio", "-i", help="Data inicial dd/MM/aaaa"),
    fim: Optional[str] = typer.Option(None, "--fim", "-f", help="Data final dd/MM/aaaa"),
):
    """Consulta uma série temporal do SGS/Bacen."""
    from brasil_cli.providers.bacen import SERIES, consultar_serie

    # Resolve nome -> código
    if serie.isdigit():
        codigo = int(serie)
        titulo = f"Série SGS #{codigo}"
    elif serie in SERIES:
        codigo = SERIES[serie]
        titulo = f"{serie.upper()} (SGS #{codigo})"
    else:
        print_error(f"Série '{serie}' não encontrada. Use 'brasil bacen series' para listar.")
        raise typer.Exit(1)

    if not ultimos and not inicio:
        ultimos = 12  # default: últimos 12 valores

    try:
        data = _run(consultar_serie(codigo, ultimos=ultimos, data_inicial=inicio, data_final=fim))
        print_series(titulo, data)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@bacen_app.command("selic")
def bacen_selic(
    ultimos: int = typer.Option(12, "--ultimos", "-n", help="Últimos N valores"),
):
    """Atalho: consulta taxa Selic meta."""
    from brasil_cli.providers.bacen import SERIES, consultar_serie

    data = _run(consultar_serie(SERIES["selic"], ultimos=ultimos))
    print_series("Taxa Selic Meta (% a.a.)", data)


@bacen_app.command("ipca")
def bacen_ipca(
    ultimos: int = typer.Option(12, "--ultimos", "-n", help="Últimos N valores"),
):
    """Atalho: consulta IPCA mensal."""
    from brasil_cli.providers.bacen import SERIES, consultar_serie

    data = _run(consultar_serie(SERIES["ipca"], ultimos=ultimos))
    print_series("IPCA Mensal (%)", data)


@bacen_app.command("cambio")
def bacen_cambio(
    ultimos: int = typer.Option(10, "--ultimos", "-n", help="Últimos N valores"),
):
    """Atalho: cotação do dólar (PTAX venda)."""
    from brasil_cli.providers.bacen import SERIES, consultar_serie

    data = _run(consultar_serie(SERIES["cambio_venda"], ultimos=ultimos))
    print_series("Dólar PTAX Venda (R$)", data)


@bacen_app.command("buscar")
def bacen_buscar(
    termo: str = typer.Argument(help="Termo para buscar no catálogo de séries (ex: pib, taxa)"),
):
    """Busca séries SGS pelo nome."""
    from brasil_cli.providers.bacen import buscar_serie

    resultado = _run(buscar_serie(termo))
    if not resultado:
        print_error(f"Nenhuma série encontrada com '{termo}'")
        raise typer.Exit(1)
    rows = [[nome, str(codigo)] for nome, codigo in sorted(resultado.items())]
    print_table(f"Séries com '{termo}'", ["Nome", "Código"], rows)


@bacen_app.command("indicadores")
def bacen_indicadores():
    """Painel com os valores mais recentes dos principais indicadores."""
    from brasil_cli.providers.bacen import indicadores_atuais

    resultado = _run(indicadores_atuais())
    nomes = {
        "selic": "Selic Meta (% a.a.)",
        "ipca": "IPCA Mensal (%)",
        "cambio_venda": "Dólar PTAX Venda (R$)",
        "cdi": "CDI Diário (%)",
        "desemprego": "Desemprego PNAD (%)",
    }
    print_kv("Indicadores Econômicos", {nomes.get(k, k): v for k, v in resultado.items()})


@bacen_app.command("focus")
def bacen_focus(
    indicador: str = typer.Argument(help="Indicador: IPCA, IGP-M, Selic, Câmbio, 'PIB Total'"),
    data_inicio: Optional[str] = typer.Option(None, "--inicio", "-i", help="Data mínima YYYY-MM-DD"),
    limite: int = typer.Option(10, "--limite", "-n", help="Número de registros"),
):
    """Expectativas de mercado do Boletim Focus."""
    from brasil_cli.providers.bacen import expectativas_focus

    try:
        data = _run(expectativas_focus(indicador, data_inicio=data_inicio, limite=limite))
        if not data:
            print_error(f"Nenhuma expectativa encontrada para '{indicador}'")
            raise typer.Exit(1)
        rows = [
            [
                d.get("Data", ""),
                d.get("DataReferencia", ""),
                str(d.get("Media", "")),
                str(d.get("Mediana", "")),
                str(d.get("Minimo", "")),
                str(d.get("Maximo", "")),
            ]
            for d in data
        ]
        print_table(
            f"Focus — {indicador}",
            ["Data", "Ref.", "Média", "Mediana", "Mín", "Máx"],
            rows,
        )
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# IBGE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@ibge_app.command("estados")
def ibge_estados():
    """Lista todos os estados brasileiros."""
    from brasil_cli.providers.ibge import listar_estados

    data = _run(listar_estados())
    rows = [[e["sigla"], e["nome"], str(e["id"])] for e in data]
    print_table("Estados do Brasil", ["UF", "Nome", "ID IBGE"], rows)


@ibge_app.command("municipios")
def ibge_municipios(
    uf: str = typer.Argument(help="Sigla do estado (ex: CE, SP)"),
):
    """Lista municípios de um estado."""
    from brasil_cli.providers.ibge import listar_municipios

    data = _run(listar_municipios(uf.upper()))
    rows = [[m["nome"], str(m["id"])] for m in data[:50]]
    caption = f"Mostrando {len(rows)} de {len(data)} municípios" if len(data) > 50 else None
    print_table(f"Municípios — {uf.upper()}", ["Nome", "ID IBGE"], rows, caption=caption)


@ibge_app.command("buscar-cidade")
def ibge_buscar_cidade(
    nome: str = typer.Argument(help="Nome (ou parte) do município"),
):
    """Busca municípios por nome."""
    from brasil_cli.providers.ibge import buscar_municipio

    data = _run(buscar_municipio(nome))
    if not data:
        print_error(f"Nenhum município encontrado com '{nome}'")
        raise typer.Exit(1)
    rows = [
        [m["nome"], m.get("microrregiao", {}).get("mesorregiao", {}).get("UF", {}).get("sigla", ""), str(m["id"])]
        for m in data[:20]
    ]
    print_table(f"Municípios com '{nome}'", ["Nome", "UF", "ID"], rows)


@ibge_app.command("nomes")
def ibge_nomes(
    nome: str = typer.Argument(help="Nome para consultar ranking"),
):
    """Ranking de frequência de um nome no Brasil."""
    from brasil_cli.providers.ibge import ranking_nomes

    data = _run(ranking_nomes(nome))
    if not data or not data[0].get("res"):
        print_error(f"Nome '{nome}' não encontrado")
        raise typer.Exit(1)
    rows = [[r["periodo"], str(r["frequencia"])] for r in data[0]["res"]]
    print_table(f"Frequência do nome '{nome}'", ["Período", "Frequência"], rows)


@ibge_app.command("populacao")
def ibge_populacao(
    localidade: str = typer.Argument("BR", help="Código IBGE ou 'BR' para Brasil"),
):
    """População estimada (IBGE tabela 6579)."""
    from brasil_cli.providers.ibge import populacao_estimada

    try:
        data = _run(populacao_estimada(localidade))
        series = data[0]["resultados"][0]["series"]
        rows = []
        for s in series:
            loc_nome = s["localidade"]["nome"]
            for periodo, valor in s["serie"].items():
                rows.append([loc_nome, periodo, valor])
        print_table("População Estimada", ["Localidade", "Período", "População"], rows)
    except Exception as e:
        print_error(f"Erro ao consultar população: {e}")
        raise typer.Exit(1)


@ibge_app.command("pib")
def ibge_pib():
    """PIB trimestral — variação % (últimos 6 períodos)."""
    from brasil_cli.providers.ibge import indicadores_pib

    try:
        data = _run(indicadores_pib())
        nome_var = data[0].get("variavel", "PIB")
        unidade = data[0].get("unidade", "%")
        series = data[0]["resultados"][0]["series"]
        rows = [[periodo, valor] for periodo, valor in series[0]["serie"].items()]
        print_table(f"{nome_var} ({unidade})", ["Período", "Variação"], rows)
    except Exception as e:
        print_error(f"Erro ao consultar PIB: {e}")
        raise typer.Exit(1)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CÂMARA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@camara_app.command("deputados")
def camara_deputados(
    nome: Optional[str] = typer.Option(None, "--nome", "-n", help="Filtrar por nome"),
    uf: Optional[str] = typer.Option(None, "--uf", "-u", help="Filtrar por UF"),
    partido: Optional[str] = typer.Option(None, "--partido", "-p", help="Filtrar por partido"),
    pagina: int = typer.Option(1, "--pagina", help="Página de resultados"),
    todos: bool = typer.Option(False, "--todos", help="Retorna todos os resultados (auto-paginação)"),
):
    """Lista/busca deputados em exercício."""
    from brasil_cli.providers.camara import buscar_deputados

    if todos:
        dados = _paginar_todos(buscar_deputados, nome=nome, sigla_uf=uf, sigla_partido=partido)
        if not dados:
            print_error("Nenhum deputado encontrado")
            raise typer.Exit(1)
        rows = [[str(d["id"]), d["nome"], d.get("siglaPartido", ""), d.get("siglaUf", "")] for d in dados]
        print_table("Deputados", ["ID", "Nome", "Partido", "UF"], rows)
        return

    resp = _run(buscar_deputados(nome=nome, sigla_uf=uf, sigla_partido=partido, pagina=pagina))
    dados = resp.get("dados", [])
    if not dados:
        print_error("Nenhum deputado encontrado")
        raise typer.Exit(1)
    rows = [
        [str(d["id"]), d["nome"], d.get("siglaPartido", ""), d.get("siglaUf", "")]
        for d in dados
    ]
    links = resp.get("links", [])
    tem_proxima = any(lnk.get("rel") == "next" for lnk in links)
    extras = "".join([f" --uf {uf}" if uf else "", f" --partido {partido}" if partido else "", f" --nome {nome}" if nome else ""])
    meta = {"page": pagina, "has_next": tem_proxima, "next_hint": f"brasil --json camara deputados{extras} --pagina {pagina + 1}"} if tem_proxima else {"page": pagina, "has_next": False}
    caption = f"Página {pagina} — use --pagina {pagina + 1} para ver mais" if tem_proxima else None
    print_table("Deputados", ["ID", "Nome", "Partido", "UF"], rows, caption=caption, meta=meta)


@camara_app.command("proposicoes")
def camara_proposicoes(
    keywords: Optional[str] = typer.Option(None, "--keywords", "-k", help="Palavras-chave"),
    tipo: Optional[str] = typer.Option(None, "--tipo", "-t", help="Tipo (PL, PEC, MPV...)"),
    ano: Optional[int] = typer.Option(None, "--ano", "-a", help="Ano"),
    pagina: int = typer.Option(1, "--pagina", help="Página"),
    todos: bool = typer.Option(False, "--todos", help="Retorna todos os resultados (auto-paginação)"),
):
    """Busca proposições legislativas."""
    from brasil_cli.providers.camara import buscar_proposicoes

    def _rows(dados: list) -> list:
        return [[str(d["id"]), f'{d.get("siglaTipo","")}{d.get("numero","")}', str(d.get("ano", "")), d.get("ementa", "")[:80]] for d in dados]

    if todos:
        dados = _paginar_todos(buscar_proposicoes, sigla_tipo=tipo, keywords=keywords, ano=ano)
        if not dados:
            print_error("Nenhuma proposição encontrada")
            raise typer.Exit(1)
        print_table("Proposições", ["ID", "Tipo/Nº", "Ano", "Ementa"], _rows(dados))
        return

    resp = _run(buscar_proposicoes(sigla_tipo=tipo, keywords=keywords, ano=ano, pagina=pagina))
    dados = resp.get("dados", [])
    if not dados:
        print_error("Nenhuma proposição encontrada")
        raise typer.Exit(1)
    links = resp.get("links", [])
    tem_proxima = any(lnk.get("rel") == "next" for lnk in links)
    extras = "".join([f" --tipo {tipo}" if tipo else "", f" --ano {ano}" if ano else "", f" --keywords '{keywords}'" if keywords else ""])
    meta = {"page": pagina, "has_next": tem_proxima, "next_hint": f"brasil --json camara proposicoes{extras} --pagina {pagina + 1}"} if tem_proxima else {"page": pagina, "has_next": False}
    caption = f"Página {pagina} — use --pagina {pagina + 1} para ver mais" if tem_proxima else None
    print_table("Proposições", ["ID", "Tipo/Nº", "Ano", "Ementa"], _rows(dados), caption=caption, meta=meta)


@camara_app.command("despesas")
def camara_despesas(
    id_deputado: int = typer.Argument(help="ID do deputado"),
    ano: Optional[int] = typer.Option(None, "--ano", "-a", help="Ano"),
    mes: Optional[int] = typer.Option(None, "--mes", "-m", help="Mês"),
):
    """Consulta despesas (cota parlamentar) de um deputado."""
    from brasil_cli.providers.camara import despesas_deputado

    resp = _run(despesas_deputado(id_deputado, ano=ano, mes=mes))
    dados = resp.get("dados", [])
    if not dados:
        print_info("Nenhuma despesa encontrada")
        return
    total = sum(float(d.get("valorDocumento", 0)) for d in dados)
    rows = [
        [
            d.get("dataDocumento", "")[:10],
            d.get("tipoDespesa", "")[:40],
            d.get("nomeFornecedor", "")[:30],
            f'R$ {float(d.get("valorDocumento", 0)):,.2f}',
        ]
        for d in dados
    ]
    print_table(
        f"Despesas — Deputado #{id_deputado}",
        ["Data", "Tipo", "Fornecedor", "Valor"],
        rows,
        caption=f"Total: R$ {total:,.2f}",
    )


@camara_app.command("deputado")
def camara_deputado(
    id_deputado: int = typer.Argument(help="ID do deputado"),
):
    """Exibe o perfil completo de um deputado."""
    from brasil_cli.providers.camara import detalhes_deputado

    try:
        resp = _run(detalhes_deputado(id_deputado))
        d = resp.get("dados", {})
        status = d.get("ultimoStatus", {})
        print_kv(f"Deputado #{id_deputado}", {
            "Nome Civil": d.get("nomeCivil", ""),
            "Nome Parlamentar": status.get("nome", ""),
            "Partido": status.get("siglaPartido", ""),
            "UF": status.get("siglaUf", ""),
            "Situação": status.get("situacao", ""),
            "E-mail": status.get("email", ""),
            "Escolaridade": d.get("escolaridade", ""),
        })
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@camara_app.command("votacoes")
def camara_votacoes(
    id_proposicao: int = typer.Argument(help="ID da proposição"),
):
    """Lista votações de uma proposição."""
    from brasil_cli.providers.camara import votacoes_proposicao

    resp = _run(votacoes_proposicao(id_proposicao))
    dados = resp.get("dados", [])
    if not dados:
        print_info("Nenhuma votação encontrada")
        return
    rows = [
        [
            str(v.get("id", "")),
            v.get("data", "")[:10],
            v.get("siglaOrgao", ""),
            v.get("descricao", "")[:60],
            "Sim" if v.get("aprovacao") == 1 else "Não" if v.get("aprovacao") == 0 else "-",
        ]
        for v in dados
    ]
    print_table(
        f"Votações — Proposição #{id_proposicao}",
        ["ID", "Data", "Órgão", "Descrição", "Aprovada"],
        rows,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BRASILAPI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@br_app.command("cep")
def br_cep(
    cep: str = typer.Argument(help="CEP para consultar (ex: 63000-000)"),
):
    """Consulta endereço por CEP."""
    from brasil_cli.providers.brasilapi import consultar_cep

    try:
        data = _run(consultar_cep(cep))
        print_kv(f"CEP {cep}", {
            "Logradouro": data.get("street", ""),
            "Bairro": data.get("neighborhood", ""),
            "Cidade": data.get("city", ""),
            "Estado": data.get("state", ""),
        })
    except Exception as e:
        print_error(f"CEP não encontrado: {e}")
        raise typer.Exit(1)


@br_app.command("cnpj")
def br_cnpj(
    cnpj: str = typer.Argument(help="CNPJ para consultar"),
):
    """Consulta dados de empresa por CNPJ."""
    from brasil_cli.providers.brasilapi import consultar_cnpj

    try:
        data = _run(consultar_cnpj(cnpj))
        print_kv(f"CNPJ {cnpj}", {
            "Razão Social": data.get("razao_social", ""),
            "Nome Fantasia": data.get("nome_fantasia", ""),
            "CNAE": f'{data.get("cnae_fiscal", "")} — {data.get("cnae_fiscal_descricao", "")}',
            "Situação": data.get("descricao_situacao_cadastral", ""),
            "Abertura": data.get("data_inicio_atividade", ""),
            "Município": f'{data.get("municipio", "")} / {data.get("uf", "")}',
            "Capital Social": f'R$ {float(data.get("capital_social", 0)):,.2f}',
        })
    except Exception as e:
        print_error(f"CNPJ não encontrado: {e}")
        raise typer.Exit(1)


@br_app.command("bancos")
def br_bancos(
    busca: Optional[str] = typer.Argument(None, help="Busca por nome (opcional)"),
):
    """Lista bancos registrados no Brasil."""
    from brasil_cli.providers.brasilapi import listar_bancos

    data = _run(listar_bancos())
    if busca:
        busca_l = busca.lower()
        data = [b for b in data if busca_l in (b.get("name") or "").lower() or busca_l in str(b.get("code", ""))]
    rows = [[str(b.get("code", "")), b.get("name", ""), b.get("fullName", "")[:50]] for b in data[:30]]
    print_table("Bancos", ["Código", "Nome", "Nome Completo"], rows)


@br_app.command("feriados")
def br_feriados(
    ano: int = typer.Argument(help="Ano (ex: 2026)"),
):
    """Lista feriados nacionais de um ano."""
    from brasil_cli.providers.brasilapi import feriados

    data = _run(feriados(ano))
    rows = [[f.get("date", ""), f.get("name", ""), f.get("type", "")] for f in data]
    print_table(f"Feriados {ano}", ["Data", "Nome", "Tipo"], rows)


@br_app.command("ddd")
def br_ddd(
    ddd: int = typer.Argument(help="Código DDD (ex: 88)"),
):
    """Lista cidades de um DDD."""
    from brasil_cli.providers.brasilapi import consultar_ddd

    data = _run(consultar_ddd(ddd))
    estado = data.get("state", "")
    cidades = data.get("cities", [])
    console.print(f"[bold]DDD {ddd}[/bold] — {estado}")
    console.print(", ".join(cidades[:40]))
    if len(cidades) > 40:
        print_info(f"... e mais {len(cidades) - 40} cidades")


@br_app.command("fipe")
def br_fipe(
    codigo: str = typer.Argument(help="Código FIPE do veículo"),
):
    """Consulta preço de veículo pela tabela FIPE."""
    from brasil_cli.providers.brasilapi import tabela_fipe

    try:
        data = _run(tabela_fipe(codigo))
        if not data:
            print_error("Código FIPE não encontrado")
            raise typer.Exit(1)
        for item in data[:5]:
            print_kv(f"FIPE {codigo}", {
                "Veículo": item.get("modelo", ""),
                "Marca": item.get("marca", ""),
                "Ano": item.get("anoModelo", ""),
                "Combustível": item.get("combustivel", ""),
                "Preço": item.get("valor", ""),
                "Referência": item.get("mesReferencia", ""),
            })
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@br_app.command("banco")
def br_banco(
    codigo: int = typer.Argument(help="Código do banco (ex: 001 para Banco do Brasil)"),
):
    """Detalhes de um banco pelo código."""
    from brasil_cli.providers.brasilapi import buscar_banco

    try:
        data = _run(buscar_banco(codigo))
        print_kv(f"Banco {codigo}", {
            "Nome": data.get("name", ""),
            "Nome Completo": data.get("fullName", ""),
            "ISPB": data.get("ispb", ""),
            "Código": str(data.get("code", "")),
        })
    except Exception as e:
        print_error(f"Banco não encontrado: {e}")
        raise typer.Exit(1)


@br_app.command("marcas-fipe")
def br_marcas_fipe(
    tipo: str = typer.Option("carros", "--tipo", "-t", help="Tipo: carros, motos, caminhoes"),
):
    """Lista marcas disponíveis na tabela FIPE."""
    from brasil_cli.providers.brasilapi import listar_marcas_fipe

    data = _run(listar_marcas_fipe(tipo))
    rows = [[m.get("nome", ""), m.get("valor", "")] for m in data[:50]]
    print_table(f"Marcas FIPE — {tipo}", ["Nome", "Código"], rows)


@br_app.command("pix")
def br_pix():
    """Lista participantes do sistema PIX."""
    from brasil_cli.providers.brasilapi import pix_participantes

    data = _run(pix_participantes())
    rows = [
        [
            p.get("ispb", ""),
            p.get("nome", "")[:50],
            p.get("nomeReduzido", ""),
            p.get("modalidadeParticipacao", ""),
        ]
        for p in data[:40]
    ]
    print_table("Participantes PIX", ["ISPB", "Nome", "Nome Reduzido", "Modalidade"], rows)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TRANSPARÊNCIA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@transparencia_app.command("contratos")
def transparencia_contratos(
    api_key: str = typer.Option(..., "--key", "-k", envvar="TRANSPARENCIA_API_KEY", help="Chave API"),
    inicio: Optional[str] = typer.Option(None, "--inicio", "-i", help="Data inicial dd/MM/aaaa"),
    fim: Optional[str] = typer.Option(None, "--fim", "-f", help="Data final dd/MM/aaaa"),
    pagina: int = typer.Option(1, "--pagina", help="Página"),
    todos: bool = typer.Option(False, "--todos", help="Retorna todos os resultados (auto-paginação)"),
):
    """Busca contratos do governo federal."""
    from brasil_cli.providers.transparencia import buscar_contratos

    def _rows(data: list) -> list:
        return [[str(c.get("id", "")), c.get("objeto", "")[:60], c.get("fornecedor", {}).get("nome", "")[:30], f'R$ {float(c.get("valorInicial", 0)):,.2f}'] for c in data]

    try:
        if todos:
            data = _paginar_todos(buscar_contratos, api_key=api_key, data_inicial=inicio, data_final=fim)
            if not data:
                print_info("Nenhum contrato encontrado")
                return
            print_table("Contratos Federais", ["ID", "Objeto", "Fornecedor", "Valor"], _rows(data))
            return

        data = _run(buscar_contratos(api_key, data_inicial=inicio, data_final=fim, pagina=pagina))
        if not data:
            print_info("Nenhum contrato encontrado")
            return
        tem_proxima = len(data) >= 15
        extras = "".join([f" --inicio {inicio}" if inicio else "", f" --fim {fim}" if fim else ""])
        meta = {"page": pagina, "has_next": tem_proxima, "next_hint": f"brasil --json transparencia contratos{extras} --pagina {pagina + 1}"} if tem_proxima else {"page": pagina, "has_next": False}
        caption = f"Página {pagina} — use --pagina {pagina + 1} para ver mais" if tem_proxima else None
        print_table("Contratos Federais", ["ID", "Objeto", "Fornecedor", "Valor"], _rows(data[:15]), caption=caption, meta=meta)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@transparencia_app.command("servidores")
def transparencia_servidores(
    api_key: str = typer.Option(..., "--key", "-k", envvar="TRANSPARENCIA_API_KEY", help="Chave API"),
    nome: Optional[str] = typer.Option(None, "--nome", "-n", help="Filtrar por nome"),
    orgao: Optional[str] = typer.Option(None, "--orgao", "-o", help="Código do órgão"),
    pagina: int = typer.Option(1, "--pagina", help="Página"),
    todos: bool = typer.Option(False, "--todos", help="Retorna todos os resultados (auto-paginação)"),
):
    """Busca servidores do governo federal."""
    from brasil_cli.providers.transparencia import buscar_servidores

    def _rows(data: list) -> list:
        return [[s.get("nome", "")[:40], s.get("descricaoCargoEfetivo", "")[:40], s.get("orgaoExercicio", {}).get("nome", "")[:35] if isinstance(s.get("orgaoExercicio"), dict) else str(s.get("orgaoExercicio", ""))[:35], f'R$ {float(s.get("remuneracaoBasicaBruta", 0)):,.2f}' if s.get("remuneracaoBasicaBruta") else ""] for s in data]

    try:
        if todos:
            data = _paginar_todos(buscar_servidores, api_key=api_key, nome=nome, orgao=orgao)
            if not data:
                print_info("Nenhum servidor encontrado")
                return
            print_table("Servidores Federais", ["Nome", "Cargo", "Órgão", "Remuneração"], _rows(data))
            return

        data = _run(buscar_servidores(api_key, nome=nome, orgao=orgao, pagina=pagina))
        if not data:
            print_info("Nenhum servidor encontrado")
            return
        tem_proxima = len(data) >= 15
        extras = "".join([f" --nome '{nome}'" if nome else "", f" --orgao {orgao}" if orgao else ""])
        meta = {"page": pagina, "has_next": tem_proxima, "next_hint": f"brasil --json transparencia servidores{extras} --pagina {pagina + 1}"} if tem_proxima else {"page": pagina, "has_next": False}
        caption = f"Página {pagina} — use --pagina {pagina + 1} para ver mais" if tem_proxima else None
        print_table("Servidores Federais", ["Nome", "Cargo", "Órgão", "Remuneração"], _rows(data[:15]), caption=caption, meta=meta)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@transparencia_app.command("despesas")
def transparencia_despesas(
    api_key: str = typer.Option(..., "--key", "-k", envvar="TRANSPARENCIA_API_KEY", help="Chave API"),
    ano: int = typer.Argument(help="Ano das despesas (ex: 2024)"),
    pagina: int = typer.Option(1, "--pagina", help="Página"),
):
    """Busca despesas do governo federal por ano."""
    from brasil_cli.providers.transparencia import buscar_despesas

    try:
        data = _run(buscar_despesas(api_key, ano=ano, pagina=pagina))
        if not data:
            print_info("Nenhuma despesa encontrada")
            return
        rows = [
            [
                d.get("codigoOrgao", ""),
                d.get("nomeOrgao", "")[:40],
                d.get("valorDespesa", "") or d.get("valor", ""),
            ]
            for d in data[:15]
        ]
        print_table(f"Despesas Federais — {ano}", ["Órgão (cod.)", "Órgão (nome)", "Valor"], rows)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@transparencia_app.command("licitacoes")
def transparencia_licitacoes(
    api_key: str = typer.Option(..., "--key", "-k", envvar="TRANSPARENCIA_API_KEY", help="Chave API"),
    orgao: Optional[str] = typer.Option(None, "--orgao", "-o", help="Código do órgão"),
    inicio: Optional[str] = typer.Option(None, "--inicio", "-i", help="Data inicial dd/MM/aaaa"),
    fim: Optional[str] = typer.Option(None, "--fim", "-f", help="Data final dd/MM/aaaa"),
    pagina: int = typer.Option(1, "--pagina", help="Página"),
    todos: bool = typer.Option(False, "--todos", help="Retorna todos os resultados (auto-paginação)"),
):
    """Busca licitações do governo federal."""
    from brasil_cli.providers.transparencia import buscar_licitacoes

    def _rows(data: list) -> list:
        return [[str(l.get("id", "")), l.get("objeto", "")[:60], l.get("modalidade", {}).get("descricao", "") if isinstance(l.get("modalidade"), dict) else str(l.get("modalidade", "")), f'R$ {float(l.get("valorLicitacao", 0)):,.2f}' if l.get("valorLicitacao") else ""] for l in data]

    try:
        if todos:
            data = _paginar_todos(buscar_licitacoes, api_key=api_key, codigo_orgao=orgao, data_inicial=inicio, data_final=fim)
            if not data:
                print_info("Nenhuma licitação encontrada")
                return
            print_table("Licitações Federais", ["ID", "Objeto", "Modalidade", "Valor"], _rows(data))
            return

        data = _run(buscar_licitacoes(api_key, codigo_orgao=orgao, data_inicial=inicio, data_final=fim, pagina=pagina))
        if not data:
            print_info("Nenhuma licitação encontrada")
            return
        tem_proxima = len(data) >= 15
        extras = "".join([f" --orgao {orgao}" if orgao else "", f" --inicio {inicio}" if inicio else "", f" --fim {fim}" if fim else ""])
        meta = {"page": pagina, "has_next": tem_proxima, "next_hint": f"brasil --json transparencia licitacoes{extras} --pagina {pagina + 1}"} if tem_proxima else {"page": pagina, "has_next": False}
        caption = f"Página {pagina} — use --pagina {pagina + 1} para ver mais" if tem_proxima else None
        print_table("Licitações Federais", ["ID", "Objeto", "Modalidade", "Valor"], _rows(data[:15]), caption=caption, meta=meta)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@transparencia_app.command("emendas")
def transparencia_emendas(
    api_key: str = typer.Option(..., "--key", "-k", envvar="TRANSPARENCIA_API_KEY", help="Chave API"),
    ano: Optional[int] = typer.Option(None, "--ano", "-a", help="Ano"),
    autor: Optional[str] = typer.Option(None, "--autor", help="Nome do autor"),
    pagina: int = typer.Option(1, "--pagina", help="Página"),
    todos: bool = typer.Option(False, "--todos", help="Retorna todos os resultados (auto-paginação)"),
):
    """Busca emendas parlamentares."""
    from brasil_cli.providers.transparencia import buscar_emendas

    def _rows(data: list) -> list:
        return [[str(e.get("codigoEmenda", "")), e.get("nomeAutor", "")[:35], e.get("localidadeGasto", "")[:30], f'R$ {float(e.get("valorEmpenhado", 0)):,.2f}' if e.get("valorEmpenhado") else ""] for e in data]

    try:
        if todos:
            data = _paginar_todos(buscar_emendas, api_key=api_key, ano=ano, nome_autor=autor)
            if not data:
                print_info("Nenhuma emenda encontrada")
                return
            print_table("Emendas Parlamentares", ["Código", "Autor", "Localidade", "Empenhado"], _rows(data))
            return

        data = _run(buscar_emendas(api_key, ano=ano, nome_autor=autor, pagina=pagina))
        if not data:
            print_info("Nenhuma emenda encontrada")
            return
        tem_proxima = len(data) >= 15
        extras = "".join([f" --ano {ano}" if ano else "", f" --autor '{autor}'" if autor else ""])
        meta = {"page": pagina, "has_next": tem_proxima, "next_hint": f"brasil --json transparencia emendas{extras} --pagina {pagina + 1}"} if tem_proxima else {"page": pagina, "has_next": False}
        caption = f"Página {pagina} — use --pagina {pagina + 1} para ver mais" if tem_proxima else None
        print_table("Emendas Parlamentares", ["Código", "Autor", "Localidade", "Empenhado"], _rows(data[:15]), caption=caption, meta=meta)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@transparencia_app.command("bolsa-familia")
def transparencia_bolsa_familia(
    api_key: str = typer.Option(..., "--key", "-k", envvar="TRANSPARENCIA_API_KEY", help="Chave API"),
    mes_ano: str = typer.Argument(help="Mês/Ano no formato MM/AAAA (ex: 01/2024)"),
    municipio: Optional[str] = typer.Option(None, "--municipio", "-m", help="Código IBGE do município"),
    pagina: int = typer.Option(1, "--pagina", help="Página"),
):
    """Consulta pagamentos do Bolsa Família por município."""
    from brasil_cli.providers.transparencia import consultar_bolsa_familia

    try:
        data = _run(consultar_bolsa_familia(api_key, mes_ano=mes_ano, codigo_ibge=municipio, pagina=pagina))
        if not data:
            print_info("Nenhum dado encontrado")
            return
        rows = [
            [
                b.get("municipio", {}).get("nomeIBGE", "") if isinstance(b.get("municipio"), dict) else str(b.get("municipio", "")),
                str(b.get("quantidade", "")),
                f'R$ {float(b.get("valor", 0)):,.2f}' if b.get("valor") else "",
            ]
            for b in data[:20]
        ]
        print_table(f"Bolsa Família — {mes_ano}", ["Município", "Beneficiários", "Valor Total"], rows)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@transparencia_app.command("viagens")
def transparencia_viagens(
    api_key: str = typer.Option(..., "--key", "-k", envvar="TRANSPARENCIA_API_KEY", help="Chave API"),
    cpf: str = typer.Argument(help="CPF do servidor (somente números)"),
    pagina: int = typer.Option(1, "--pagina", help="Página"),
):
    """Busca viagens a serviço de um servidor."""
    from brasil_cli.providers.transparencia import buscar_viagens

    try:
        data = _run(buscar_viagens(api_key, cpf=cpf, pagina=pagina))
        if not data:
            print_info("Nenhuma viagem encontrada")
            return
        rows = [
            [
                v.get("dataPartida", "")[:10] if v.get("dataPartida") else "",
                v.get("destinos", [{}])[0].get("destino", "") if v.get("destinos") else "",
                v.get("motivo", "")[:50],
                f'R$ {float(v.get("valorPassagens", 0)):,.2f}' if v.get("valorPassagens") else "",
            ]
            for v in data[:15]
        ]
        print_table(f"Viagens — CPF {cpf}", ["Partida", "Destino", "Motivo", "Passagens"], rows)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@transparencia_app.command("sancoes")
def transparencia_sancoes(
    api_key: str = typer.Option(..., "--key", "-k", envvar="TRANSPARENCIA_API_KEY", help="Chave API"),
    consulta: str = typer.Argument(help="CNPJ ou CPF para consultar sanções (CEIS)"),
    pagina: int = typer.Option(1, "--pagina", help="Página"),
):
    """Consulta sanções no CEIS (Cadastro de Empresas Inidôneas e Suspensas)."""
    from brasil_cli.providers.transparencia import buscar_sancoes

    try:
        data = _run(buscar_sancoes(api_key, consulta=consulta, pagina=pagina))
        if not data:
            print_info("Nenhuma sanção encontrada")
            return
        rows = [
            [
                s.get("nomeInfrator", "")[:40],
                s.get("cpfCnpjInfrator", ""),
                s.get("tipoSancao", {}).get("descricaoResumida", "") if isinstance(s.get("tipoSancao"), dict) else "",
                s.get("dataInicioSancao", "")[:10] if s.get("dataInicioSancao") else "",
                s.get("dataFimSancao", "")[:10] if s.get("dataFimSancao") else "indefinido",
            ]
            for s in data[:15]
        ]
        print_table("Sanções — CEIS", ["Nome", "CPF/CNPJ", "Tipo", "Início", "Fim"], rows)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SENADO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@senado_app.command("senadores")
def senado_senadores(
    nome: Optional[str] = typer.Option(None, "--nome", "-n", help="Filtrar por nome"),
    partido: Optional[str] = typer.Option(None, "--partido", "-p", help="Filtrar por partido"),
    uf: Optional[str] = typer.Option(None, "--uf", "-u", help="Filtrar por UF"),
):
    """Lista senadores em exercício."""
    from brasil_cli.providers.senado import listar_senadores

    data = _run(listar_senadores())
    if nome:
        data = [s for s in data if nome.lower() in s.get("IdentificacaoParlamentar", {}).get("NomeParlamentar", "").lower()]
    if partido:
        data = [s for s in data if partido.upper() == s.get("IdentificacaoParlamentar", {}).get("SiglaPartidoParlamentar", "").upper()]
    if uf:
        data = [s for s in data if uf.upper() == s.get("IdentificacaoParlamentar", {}).get("UfParlamentar", "").upper()]
    if not data:
        print_error("Nenhum senador encontrado")
        raise typer.Exit(1)
    rows = [
        [
            s.get("IdentificacaoParlamentar", {}).get("CodigoParlamentar", ""),
            s.get("IdentificacaoParlamentar", {}).get("NomeParlamentar", ""),
            s.get("IdentificacaoParlamentar", {}).get("SiglaPartidoParlamentar", ""),
            s.get("IdentificacaoParlamentar", {}).get("UfParlamentar", ""),
        ]
        for s in data
    ]
    print_table("Senadores em Exercício", ["Código", "Nome", "Partido", "UF"], rows)


@senado_app.command("senador")
def senado_senador(
    codigo: str = typer.Argument(help="Código do senador"),
):
    """Exibe perfil de um senador."""
    from brasil_cli.providers.senado import detalhes_senador

    try:
        s = _run(detalhes_senador(codigo))
        ident = s.get("IdentificacaoParlamentar", {})
        print_kv(f"Senador #{codigo}", {
            "Nome": ident.get("NomeParlamentar", ""),
            "Nome Civil": ident.get("NomeCompletoParlamentar", ""),
            "Partido": ident.get("SiglaPartidoParlamentar", ""),
            "UF": ident.get("UfParlamentar", ""),
            "E-mail": ident.get("EmailParlamentar", ""),
        })
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@senado_app.command("materias")
def senado_materias(
    tipo: Optional[str] = typer.Option(None, "--tipo", "-t", help="Sigla do tipo (PEC, PLS, PL...)"),
    ano: Optional[int] = typer.Option(None, "--ano", "-a", help="Ano"),
    keywords: Optional[str] = typer.Option(None, "--keywords", "-k", help="Palavras na ementa"),
    pagina: int = typer.Option(1, "--pagina", help="Página"),
    todos: bool = typer.Option(False, "--todos", help="Retorna todos os resultados (auto-paginação)"),
):
    """Busca matérias legislativas no Senado."""
    from brasil_cli.providers.senado import buscar_materias

    def _normalizar(raw) -> list:
        if isinstance(raw, dict):
            return [raw]
        return raw or []

    def _rows(data: list) -> list:
        return [[m.get("CodigoMateria", ""), f'{m.get("SiglaSubtipoMateria", m.get("DescricaoSubtipoMateria", ""))} {m.get("NumeroMateria", "")}/{m.get("AnoMateria", "")}', m.get("EmentaMateria", "")[:70]] for m in data]

    if todos:
        data = _normalizar(_run(buscar_materias(sigla_tipo=tipo, ano=ano, keywords=keywords, pagina=1)))
        if not data:
            print_error("Nenhuma matéria encontrada")
            raise typer.Exit(1)
        print_table("Matérias — Senado", ["Código", "Tipo/Nº/Ano", "Ementa"], _rows(data))
        return

    data = _normalizar(_run(buscar_materias(sigla_tipo=tipo, ano=ano, keywords=keywords, pagina=pagina)))
    if not data:
        print_error("Nenhuma matéria encontrada")
        raise typer.Exit(1)
    tem_proxima = len(data) >= 20
    extras = "".join([f" --tipo {tipo}" if tipo else "", f" --ano {ano}" if ano else "", f" --keywords '{keywords}'" if keywords else ""])
    meta = {"page": pagina, "has_next": tem_proxima, "next_hint": f"brasil --json senado materias{extras} --pagina {pagina + 1}"} if tem_proxima else {"page": pagina, "has_next": False}
    caption = f"Página {pagina} — use --pagina {pagina + 1} para ver mais" if tem_proxima else None
    print_table("Matérias — Senado", ["Código", "Tipo/Nº/Ano", "Ementa"], _rows(data[:20]), caption=caption, meta=meta)


@senado_app.command("votacoes")
def senado_votacoes(
    ano: str = typer.Argument(help="Ano (ex: 2024)"),
):
    """Lista votações plenárias de um ano."""
    from brasil_cli.providers.senado import listar_votacoes

    data = _run(listar_votacoes(ano))
    if not data:
        print_info("Nenhuma votação encontrada")
        return
    if isinstance(data, dict):
        data = [data]
    rows = [
        [
            v.get("CodigoSessaoVotacao", ""),
            v.get("DataSessao", "")[:10],
            v.get("DescricaoVotacao", "")[:60],
            v.get("DescricaoResultado", ""),
        ]
        for v in data[:20]
    ]
    print_table(f"Votações Plenárias — {ano}", ["Código", "Data", "Descrição", "Resultado"], rows)


@senado_app.command("comissoes")
def senado_comissoes():
    """Lista comissões atuais do Senado."""
    from brasil_cli.providers.senado import listar_comissoes

    data = _run(listar_comissoes())
    if not data:
        print_error("Nenhuma comissão encontrada")
        raise typer.Exit(1)
    if isinstance(data, dict):
        data = [data]
    rows = [
        [
            c.get("CodigoComissao", ""),
            c.get("SiglaComissao", ""),
            c.get("NomeComissao", "")[:60],
            c.get("TipoComissao", ""),
        ]
        for c in data
    ]
    print_table("Comissões do Senado", ["Código", "Sigla", "Nome", "Tipo"], rows)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ROOT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@app.command("versao")
def versao():
    """Mostra versão da CLI."""
    from brasil_cli import __version__
    console.print(f"brasil-cli v{__version__}")


def main():
    app()


if __name__ == "__main__":
    main()
