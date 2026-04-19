# 🇧🇷 brasil-cli

CLI para consulta de APIs públicas brasileiras, direto do terminal.

Inspirado na arquitetura do [mcp-brasil](https://github.com/jxnxts/mcp-brasil), mas como ferramenta CLI standalone — sem depender de MCP servers ou LLMs.

## Instalação

```bash
# Via pip (editable)
git clone <repo>
cd brasil-cli
pip install -e .

# Ou direto
pip install -e ".[dev]"  # com ferramentas de dev
```

## Uso

```bash
brasil --help
```

### Banco Central (Bacen)

```bash
# Listar séries disponíveis
brasil bacen series

# Consultar Selic (últimos 12 valores)
brasil bacen selic

# IPCA mensal (últimos 6)
brasil bacen ipca -n 6

# Câmbio dólar
brasil bacen cambio

# Qualquer série por código SGS
brasil bacen consultar 433 -n 10

# Série por período
brasil bacen consultar selic --inicio 01/01/2024 --fim 31/12/2024
```

### IBGE

```bash
# Listar estados
brasil ibge estados

# Municípios do Ceará
brasil ibge municipios CE

# Buscar cidade por nome
brasil ibge buscar-cidade "Sobral"

# Frequência de um nome
brasil ibge nomes marcos
```

### Câmara dos Deputados

```bash
# Buscar deputados
brasil camara deputados
brasil camara deputados --uf CE --partido PT

# Buscar proposições
brasil camara proposicoes --keywords "inteligência artificial" --ano 2024
brasil camara proposicoes --tipo PL --ano 2024

# Despesas de um deputado (cota parlamentar)
brasil camara despesas 12345 --ano 2024
```

### BrasilAPI

```bash
# CEP
brasil br cep 63000-000

# CNPJ
brasil br cnpj 00.000.000/0001-91

# Bancos
brasil br bancos
brasil br bancos "nubank"

# Feriados
brasil br feriados 2026

# DDD
brasil br ddd 88

# Tabela FIPE
brasil br fipe 001004-9
```

### Portal da Transparência

Requer chave de API (gratuita). Exporte como variável ou passe via `--key`:

```bash
export TRANSPARENCIA_API_KEY="sua-chave"
brasil transparencia contratos --inicio 01/01/2024 --fim 31/12/2024
```

## Arquitetura

```
brasil_cli/
├── cli.py              # Entry point Typer com todos os comandos
├── http_client.py      # httpx async com retry + backoff
├── output.py           # Formatação Rich (tabelas, painéis, séries)
└── providers/          # Um módulo por fonte de dados
    ├── bacen.py        # SGS — Selic, IPCA, câmbio, CDI, PIB
    ├── ibge.py         # Localidades, população, nomes
    ├── camara.py       # Deputados, proposições, despesas
    ├── brasilapi.py    # CEP, CNPJ, bancos, feriados, FIPE, PIX
    └── transparencia.py # Contratos, servidores, despesas federais
```

Cada provider é independente e async. A CLI usa `asyncio.run()` para bridgear o sync do Typer com os providers async — permitindo reuso dos providers em outros contextos (bots, scripts, APIs).

## Adicionando um novo provider

1. Crie `brasil_cli/providers/novo.py` com funções async
2. Adicione um `typer.Typer()` em `cli.py`
3. Registre com `app.add_typer(novo_app, name="novo")`

## Stack

- **Typer** — CLI framework com auto-complete e help
- **httpx** — HTTP client async
- **Rich** — Output formatado com tabelas e cores
- **Pydantic** (opcional) — Validação de schemas

## Licença

MIT
