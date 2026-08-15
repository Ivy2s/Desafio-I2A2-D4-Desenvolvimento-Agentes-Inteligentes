# Data Assistent

Interface React para consultar CSVs com um agente LangChain/Gemini. O fluxo é upload de CSV/ZIP na Interface A, processamento automático no FastAPI e consulta em linguagem natural na Interface B.

## Requisitos

Python 3.11+ com `venv`/`ensurepip`, Node.js 20+ e `GOOGLE_API_KEY` no backend para consultas reais. A chave nunca deve ser configurada no frontend.

## Execução

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export GOOGLE_API_KEY='sua-chave'
uvicorn api.main:app --reload
```

Em outro terminal:

```bash
cd frontend
npm ci
npm run dev
```

Use `VITE_API_BASE_URL` para apontar o frontend para outro host de API.

## API e testes

A API expõe `GET /api/health`, upload `POST /api/datasets`, metadata `GET /api/datasets/{dataset_id}` e consulta `POST /api/datasets/{dataset_id}/query`. Datasets são isolados por UUID e mantidos em memória/`.runtime` até o restart.

```bash
pytest -q
cd frontend
npm test
npm run lint
npm run build
npm run e2e
```

O E2E inicia FastAPI e Vite reais, usa Chromium e não usa mocks de resposta.

## Dicionário no ZIP

Além de um ou mais CSVs, o ZIP pode conter `dicionario.csv` (também aceitos `data_dictionary.csv` e `dictionary.csv`) com as colunas `arquivo`, `coluna` e `descricao`. O arquivo é processado como metadado e não é contado como dataset.

## Arquitetura e entrega

O frontend usa `HttpDataAssistantGateway`; a API cria uma sessão UUID isolada, `DatasetService` carrega os dados e `QueryService` orquestra o agente, que usa `describe_data` e `query_data` sobre o `DataManager` da sessão. Consulte `docs/arquitetura.md`, `docs/api_contract.md` e `docs/challenge_compliance_matrix.md`. O relatório e os artefatos de QA ficam em `deliverables/`.

Limitações conhecidas: registry/datasets efêmeros, sem autenticação e sem persistência após restart.
