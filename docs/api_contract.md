# Contrato HTTP

Baseline público para a futura integração do frontend. Os nomes JSON usam
camelCase; os datasets são efêmeros e ficam em registry de memória.

## Health

`GET /api/health`

```json
{"status":"ok","aiConfigured":false}
```

`aiConfigured` indica somente a presença da configuração do provedor; não é um
teste de conectividade.

O backend suporta os perfis `primary` e `alternative` por `GEMINI_PROFILE`.
`primary` usa `GOOGLE_API_KEY`/`GEMINI_MODEL`; `alternative` usa
`GOOGLE_API_KEY_ALT` (ou a chave primária) e `GEMINI_MODEL_ALT`.

## Upload

`POST /api/datasets` com `multipart/form-data` e campo `file` (`.csv` ou `.zip`).

Retorna `201 Created`:

```json
{
  "datasetId": "uuid",
  "status": "ready",
  "createdAt": "2026-08-14T21:00:00Z",
  "summary": {"files": 1, "rows": 565, "columns": 3},
  "datasets": [{
    "name": "vendas",
    "rows": 565,
    "columnCount": 3,
    "columns": [
      {"name": "produto", "type": "string"},
      {"name": "quantidade", "type": "string"},
      {"name": "valor", "type": "string"}
    ]
  }]
}
```

`summary.files` é a quantidade de CSVs carregados, `summary.rows` é a soma de
suas linhas e `summary.columns` é a soma de suas quantidades de colunas. Não é
uma contagem de colunas únicas entre datasets.

## Metadata

`GET /api/datasets/{dataset_id}` retorna o mesmo contrato de upload: `datasetId`,
`status`, `createdAt`, `summary` e `datasets`. O estado público atual é somente
`ready`, pois o processamento é síncrono.

## Query

`POST /api/datasets/{dataset_id}/query`

Request:

```json
{"question":"Qual é o valor total por fornecedor?"}
```

`question` é obrigatória, recebe trim, aceita até 4.000 caracteres e não pode
ser vazia.

Resposta textual:

```json
{"answer":"Não há resultado estruturado.","data":null}
```

Resposta de contagem:

```json
{"answer":"Foram encontrados 565 registros.","data":{"type":"count","value":565}}
```

Resposta tabular:

```json
{
  "answer":"Valores agrupados.",
  "data":{
    "type":"table",
    "columns":["fornecedor","valor_total"],
    "rows":[{"fornecedor":"Empresa A","valor_total":1234.5}],
    "truncated":false,
    "returnedRows":1
  }
}
```

`data` é uma união discriminada por `type`: atualmente `count` ou `table`.
`truncated` informa quando o limite público de `MAX_QUERY_RESULT_ROWS` foi
aplicado; `returnedRows` informa a quantidade efetivamente retornada.
Gráficos não fazem parte do contrato; o frontend os deriva de `TableData`
quando há uma dimensão categórica e uma métrica numérica.

## JSON seguro

Resultados estruturados convertem tipos Pandas/NumPy para tipos JSON. Inteiros
e floats numéricos viram tipos nativos, datas viram ISO-8601, valores ausentes
(`NaN`, `Infinity`, `-Infinity`, `pd.NA` e `NaT`) viram `null`.

## Erros

Todos os erros dos endpoints usam:

```json
{"error":{"code":"...","message":"...","details":null}}
```

| Código | Status | Significado |
| --- | ---: | --- |
| `validation_error` | 422 | Request inválido |
| `dataset_not_found` | 404 | UUID válido não registrado |
| `unsupported_file_type` | 415 | Arquivo diferente de CSV/ZIP |
| `upload_too_large` | 413 | Upload excede o limite |
| `invalid_zip` | 400 | ZIP corrompido |
| `unsafe_zip_entry` | 400 | Membro ZIP inseguro |
| `no_csv_files_found` | 400 | ZIP sem CSV utilizável |
| `zip_limit_exceeded` | 400 | Limite de ZIP excedido |
| `dataset_load_failed` | 400 | Falha de leitura/validação |
| `internal_error` | 500 | Falha interna não detalhada |
| `ai_provider_unavailable` | 503 | IA não configurada |
| `unknown_tool` | 502 | Agente solicitou tool não registrada |
| `tool_execution_failed` | 502 | Tool não conseguiu executar |
| `agent_timeout` | 502 | Provedor excedeu timeout |
| `agent_iteration_limit` | 502 | Agente excedeu iterações |
| `query_execution_error` | 502 | Falha genérica da consulta |

## Limitações

- Registry e datasets são perdidos no restart.
- Processamento é síncrono.
- Não há autenticação ou persistência.
- O backend fornece dados; a decisão de visualização pertence ao frontend.
