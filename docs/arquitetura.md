# Arquitetura

```mermaid
flowchart TD
  A[React - Interface A: upload] --> G[HttpDataAssistantGateway]
  G --> API[FastAPI]
  API --> DS[DatasetService]
  API --> QS[QueryService]
  DS --> P[Pipeline: ZIP, CSV, dicionário, validação]
  QS --> AG[LangChain + Gemini agent]
  AG --> T[describe_data / query_data]
  T --> DM[DataManager da sessão UUID]
  DM --> D[(Pandas CSVs)]
  QS --> R[QueryResponse]
  R --> B[React - Interface B: texto, tabela e gráfico derivado]
```

O upload é validado, extraído em diretório isolado e processado
síncronamente. `dicionario.csv` é reconhecido como metadado opcional e suas
descrições são incorporadas ao `describe_data`.

O agente recebe `SYSTEM_PROMPT`, escolhe `describe_data` ou `query_data`, recebe
o resultado da ferramenta e produz a resposta final. `QueryService` limita
iterações, timeout e retries. A UI nunca recebe a chave do Gemini.
