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

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload
```

`GOOGLE_API_KEY` é opcional para iniciar a aplicação. Ela é necessária somente
para `POST /api/datasets/{dataset_id}/query`.

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
