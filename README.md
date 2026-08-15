### Dados de teste

Os datasets fornecidos pelo curso não são versionados neste

repositório devido ao tamanho dos arquivos.

Para testar localmente:

1. Baixe os datasets disponibilizados pelo curso.

2. Coloque o ZIP em `data/raw/`.

3. Execute a aplicação.

4. Faça o upload do ZIP pela Interface A.

## API local

A API FastAPI mantém datasets carregados em memória e em `.runtime/datasets/`.
Esse armazenamento é efêmero e é perdido quando o processo reinicia.
O campo `summary.columns` representa a soma das colunas declaradas por cada
CSV carregado; as colunas efetivas de cada dataset permanecem em `datasets`.
Cada upload usa um UUID e um `DataManager` exclusivo. O diretório `data/`
continua reservado aos dados de exemplo e ao fluxo legado, não sendo usado
para uploads HTTP.

ZIPs são extraídos somente depois de validar caminhos, tipos de entrada,
duplicidades e limites. CSVs em subdiretórios são aceitos. Os limites padrão
podem ser alterados por `MAX_UPLOAD_BYTES`, `MAX_ZIP_MEMBERS`,
`MAX_ZIP_MEMBER_BYTES` e `MAX_ZIP_UNCOMPRESSED_BYTES` (500 MiB, 1.000
entradas, 500 MiB por membro e 1 GiB descompactado, respectivamente).
Consultas retornam no máximo `MAX_QUERY_RESULT_ROWS` linhas (1.000 por padrão)
e informam `truncated`/`returnedRows` em `TableData`.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload
```

`GOOGLE_API_KEY` é opcional para iniciar a aplicação. Ela é necessária somente
para `POST /api/datasets/{dataset_id}/query`.

Uma consulta é executada pelo `QueryService`, que envia `SYSTEM_PROMPT` e a
pergunta ao Gemini, executa somente `describe_data`/`query_data` vinculadas ao
dataset da sessão e reinjeta os resultados no modelo até a resposta final.
O limite padrão é de 5 iterações, com timeout de 60 segundos por chamada e até
2 retries do wrapper Gemini. Esses valores podem ser ajustados por
`MAX_AGENT_ITERATIONS`, `AGENT_REQUEST_TIMEOUT_SECONDS` e `AGENT_RETRIES`.

Endpoints disponíveis:

- `GET /api/health`
- `POST /api/datasets` com `multipart/form-data` e campo `file` (`.csv` ou `.zip`)
- `GET /api/datasets/{dataset_id}`
- `POST /api/datasets/{dataset_id}/query` com `{"question": "..."}`

Erros HTTP customizados usam o formato `{"error": {"code": "...", "message": "..."}}`.

Os testes podem ser executados com:

```bash
pytest -q
```
