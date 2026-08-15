# Relatório Técnico - Desafio I2A2 D4

## Solução

O Data Assistent recebe CSV ou ZIP pela Interface A. O FastAPI cria uma sessão
UUID, valida e extrai o conteúdo, reconhece CSVs e um eventual `dicionario.csv`.
Na Interface B, a pergunta natural é enviada ao `QueryService`, que executa um
agente LangChain com `ChatGoogleGenerativeAI` e as tools `describe_data` e
`query_data`. O resultado retorna como texto ou resposta estruturada e o
frontend deriva tabela e gráfico quando apropriado.

## Framework e agente

LangChain foi usado para o binding de tools e o loop de mensagens do agente.
`SYSTEM_PROMPT` exige descoberta do dataset antes da consulta e proíbe inventar
colunas ou dados. O serviço aplica limite de iterações, timeout e retries.
`DataManager` é sempre o da sessão UUID ativa.

## Dicionário

O ZIP de certificação contém `compras.csv`, `fornecedores.csv` e
`dicionario.csv`. O dicionário usa `arquivo,coluna,descricao`; é processado como
metadado, não como CSV consultável. A cobertura está em
`tests/test_pipeline.py` e `tests/test_api.py`.

## QA e evidências

Backend: 48 testes aprovados. Frontend: 31 testes aprovados, lint e build
aprovados. Playwright Chromium e mobile 320 px aprovaram upload real, transição
de interface, formato inválido e uma pergunta Gemini real. A aplicação retornou
count 4 para o fixture de quatro registros.

## Limitação de certificação

O segundo request da tentativa de quatro perguntas reais expirou no provedor
Gemini. Por isso este documento registra `DELIVERY_BLOCKED`, não inventa
respostas e não afirma tabela/gráfico real certificados. Para concluir, execute
`cd frontend && npm run e2e` com uma credencial Gemini estável, registre quatro
perguntas e suas respostas, atualize a matriz, gere o PDF e marque o checklist.

## Execução

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload
cd frontend && npm ci && npm run dev
```

`GOOGLE_API_KEY` fica somente no backend; `VITE_API_BASE_URL` aponta para a API.
O agente respondeu uma consulta real com 7 registros totais, sendo 4 em
`compras` e 3 em `fornecedores`.
