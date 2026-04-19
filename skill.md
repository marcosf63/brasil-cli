# brasil-cli — Skill para Agentes de AI

CLI para consultar APIs públicas brasileiras diretamente do terminal.

## Instalação

```bash
uv tool install /caminho/para/brasil-cli
```

## Flags globais obrigatórias para agentes

| Flag | Descrição |
|------|-----------|
| `--json` | Saída em JSON estruturado (sempre use em contexto de agente) |
| `--todos` | Auto-paginação — retorna **todos** os resultados em uma única chamada |

## Paginação — como detectar e navegar

Quando `--todos` não é usado, o JSON pode conter um campo `_pagination`:

```json
{
  "title": "Deputados",
  "data": [...],
  "_pagination": {
    "page": 1,
    "has_next": true,
    "next_hint": "brasil --json camara deputados --uf SP --pagina 2"
  }
}
```

**Regra:** se `_pagination.has_next == true`, execute `_pagination.next_hint` para obter a próxima página. Repita até `has_next == false`. Ou use `--todos` para receber tudo de uma vez.

---

## Referência de comandos

### Banco Central (Bacen)

```bash
# Painel de indicadores atuais (Selic, IPCA, câmbio, CDI, desemprego)
brasil --json bacen indicadores

# Séries temporais
brasil --json bacen selic [-n N]
brasil --json bacen ipca [-n N]
brasil --json bacen cambio [-n N]
brasil --json bacen consultar <serie_ou_codigo> [-n N] [--inicio dd/MM/aaaa] [--fim dd/MM/aaaa]

# Buscar série por nome
brasil --json bacen buscar <termo>

# Expectativas Focus
brasil --json bacen focus <indicador> [--inicio YYYY-MM-DD] [-n N]
# indicador: IPCA | IGP-M | Selic | Câmbio | "PIB Total"
```

### IBGE

```bash
brasil --json ibge estados
brasil --json ibge municipios <UF>
brasil --json ibge buscar-cidade <nome>
brasil --json ibge populacao [codigo_ibge_ou_BR]
brasil --json ibge pib
brasil --json ibge nomes <nome>
```

### Câmara dos Deputados

```bash
# Listagens paginadas — suportam --todos
brasil --json camara deputados [--uf UF] [--partido P] [--nome N] [--todos]
brasil --json camara proposicoes [--keywords K] [--tipo T] [--ano A] [--todos]

# Recursos individuais
brasil --json camara deputado <id>
brasil --json camara despesas <id_deputado> [--ano A] [--mes M]
brasil --json camara votacoes <id_proposicao>
```

### Senado Federal

```bash
brasil --json senado senadores [--uf UF] [--partido P] [--nome N]
brasil --json senado senador <codigo>
brasil --json senado materias [--tipo T] [--ano A] [--keywords K] [--todos]
brasil --json senado votacoes <ano>
brasil --json senado comissoes
```

### BrasilAPI

```bash
brasil --json br cep <CEP>
brasil --json br cnpj <CNPJ>
brasil --json br banco <codigo>
brasil --json br bancos [busca]
brasil --json br feriados <ano>
brasil --json br ddd <ddd>
brasil --json br fipe <codigo_fipe>
brasil --json br marcas-fipe [--tipo carros|motos|caminhoes]
brasil --json br pix
```

### Portal da Transparência

> Requer chave de API (gratuita em portaldatransparencia.gov.br).
> Passe via `--key` ou variável de ambiente `TRANSPARENCIA_API_KEY`.

```bash
# Paginados — suportam --todos
brasil --json transparencia contratos [--inicio dd/MM/aaaa] [--fim dd/MM/aaaa] [--orgao cod] [--todos]
brasil --json transparencia servidores [--nome N] [--orgao cod] [--todos]
brasil --json transparencia licitacoes [--orgao cod] [--inicio d] [--fim d] [--todos]
brasil --json transparencia emendas [--ano A] [--autor nome] [--todos]

# Outros
brasil --json transparencia despesas <ano>
brasil --json transparencia bolsa-familia <MM/AAAA> [--municipio codigo_ibge]
brasil --json transparencia viagens <cpf>
brasil --json transparencia sancoes <cnpj_ou_cpf>
```

---

## Exemplos de uso em agente

```python
import subprocess, json

def brasil(cmd: str) -> dict:
    result = subprocess.run(
        f"brasil --json {cmd}",
        shell=True, capture_output=True, text=True
    )
    return json.loads(result.stdout)

# Todos os deputados de SP de uma vez
deputados = brasil("camara deputados --uf SP --todos")
print(f"{len(deputados['data'])} deputados encontrados")

# Navegar por páginas manualmente
page = brasil("camara proposicoes --tipo PL --ano 2024")
while page.get("_pagination", {}).get("has_next"):
    hint = page["_pagination"]["next_hint"].replace("brasil --json ", "")
    page = brasil(hint)
    # processar page["data"]...

# Indicadores econômicos
indicadores = brasil("bacen indicadores")
selic = indicadores["data"]["selic"]
```
