# 🇧🇷 brasil-cli

CLI para consulta de APIs públicas brasileiras, direto do terminal.

Inspirado na arquitetura do [mcp-brasil](https://github.com/jxnxts/mcp-brasil), mas como ferramenta CLI standalone — sem depender de MCP servers ou LLMs.

## Instalação

```bash
git clone https://github.com/marcosf63/brasil-cli.git
cd brasil-cli
uv tool install .
```

Para desenvolvimento:

```bash
uv pip install -e ".[dev]"
```

## Uso

```bash
brasil --help
```

## Uso com Agentes de AI

Esta CLI foi projetada para ser consumida por agentes de AI e LLMs. Consulte o [skill.md](skill.md) para a documentação completa de uso com agentes, incluindo:

- Flag `--json` para output estruturado
- Flag `--todos` para auto-paginação
- Metadados de paginação no JSON (`_pagination`)
- Exemplos de integração em Python

## Comandos

### Banco Central (Bacen)

```bash
# Painel de indicadores atuais
brasil bacen indicadores

# Séries temporais
brasil bacen selic [-n N]
brasil bacen ipca [-n N]
brasil bacen cambio [-n N]
brasil bacen consultar <serie_ou_codigo> [-n N] [--inicio dd/MM/aaaa] [--fim dd/MM/aaaa]

# Buscar série por nome no catálogo SGS
brasil bacen buscar <termo>

# Expectativas de mercado — Boletim Focus
brasil bacen focus <IPCA|Selic|Câmbio|"PIB Total"> [--inicio YYYY-MM-DD]

# Listar séries pré-cadastradas
brasil bacen series
```

### IBGE

```bash
brasil ibge estados
brasil ibge municipios <UF>
brasil ibge buscar-cidade <nome>
brasil ibge populacao [codigo_ibge]
brasil ibge pib
brasil ibge nomes <nome>
```

### Câmara dos Deputados

```bash
brasil camara deputados [--uf UF] [--partido P] [--nome N] [--todos]
brasil camara proposicoes [--keywords K] [--tipo T] [--ano A] [--todos]
brasil camara deputado <id>
brasil camara despesas <id_deputado> [--ano A] [--mes M]
brasil camara votacoes <id_proposicao>
```

### Senado Federal

```bash
brasil senado senadores [--uf UF] [--partido P] [--nome N]
brasil senado senador <codigo>
brasil senado materias [--tipo T] [--ano A] [--keywords K] [--todos]
brasil senado votacoes <ano>
brasil senado comissoes
```

### BrasilAPI

```bash
brasil br cep <CEP>
brasil br cnpj <CNPJ>
brasil br banco <codigo>
brasil br bancos [busca]
brasil br feriados <ano>
brasil br ddd <ddd>
brasil br fipe <codigo_fipe>
brasil br marcas-fipe [--tipo carros|motos|caminhoes]
brasil br pix
```

### Portal da Transparência

Requer chave de API gratuita em [portaldatransparencia.gov.br](https://portaldatransparencia.gov.br/api-de-dados).
Exporte como variável ou passe via `--key`:

```bash
export TRANSPARENCIA_API_KEY="sua-chave"

brasil transparencia contratos [--inicio dd/MM/aaaa] [--fim dd/MM/aaaa] [--todos]
brasil transparencia servidores [--nome N] [--orgao cod] [--todos]
brasil transparencia despesas <ano>
brasil transparencia licitacoes [--orgao cod] [--todos]
brasil transparencia emendas [--ano A] [--autor nome] [--todos]
brasil transparencia bolsa-familia <MM/AAAA> [--municipio codigo_ibge]
brasil transparencia viagens <cpf>
brasil transparencia sancoes <cnpj_ou_cpf>
```

## Flags globais

| Flag | Descrição |
|------|-----------|
| `--json` | Output em JSON estruturado (ideal para scripts e agentes de AI) |
| `--todos` | Auto-paginação — retorna todos os resultados de uma vez |

```bash
# Output JSON
brasil --json bacen indicadores
brasil --json camara deputados --uf SP

# Todos os resultados sem paginação
brasil --json camara deputados --uf SP --todos
```

## Arquitetura

```
brasil_cli/
├── cli.py              # Entry point Typer com todos os comandos
├── http_client.py      # httpx async com retry + backoff exponencial
├── output.py           # Formatação Rich (tabelas, painéis, séries) e modo JSON
└── providers/          # Um módulo por fonte de dados
    ├── bacen.py        # SGS — Selic, IPCA, câmbio, CDI, PIB, Focus
    ├── ibge.py         # Localidades, população, nomes, PIB
    ├── camara.py       # Deputados, proposições, votações, despesas
    ├── brasilapi.py    # CEP, CNPJ, bancos, feriados, FIPE, PIX
    ├── senado.py       # Senadores, matérias, votações, comissões
    └── transparencia.py # Contratos, servidores, licitações, emendas, Bolsa Família
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

## Licença

MIT
