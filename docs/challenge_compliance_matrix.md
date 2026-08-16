# Matriz de Conformidade

| ID | Requisito oficial | Implementação | Teste/Evidência | Estado |
| -- | ----------------- | ------------- | --------------- | ------ |
| REQ-01 | MVP executável com agente | React, FastAPI e agente LangChain | Playwright upload/query real; pytest | PASS |
| REQ-02 | Duas interfaces | Upload e workspace de consulta | `acceptance.spec.ts` | PASS |
| REQ-03 | Upload de ZIP | `DatasetService` e `ZipHandler` | E2E ZIP canônico | PASS |
| REQ-04 | Um ou mais CSVs | CSVs raiz/subdiretório; múltiplos arquivos | fixture com 2 CSVs | PASS |
| REQ-05 | Dicionário de dados no ZIP | `dicionario.csv` reconhecido e enviado ao `describe_data` | `test_pipeline_processes_provided_data_dictionary`, E2E upload | PASS |
| REQ-06 | Processamento automático | upload síncrono prepara sessão | E2E transição após upload | PASS |
| REQ-07 | Consulta disponível | workspace e composer após CTA de exploração | E2E Interface B | PASS |
| REQ-08 | Linguagem natural | textarea encaminha pergunta ao endpoint | E2E query real | PASS |
| REQ-09 | Agente inteligente | Groq/Gemini com tools vinculadas | `agents/csv_agent.py`, E2E real canônico | PASS |
| REQ-10 | Interpretação e consulta estruturada | `describe_data`/`query_data` escolhidas pelo modelo | testes do agente; uma chamada real | PASS |
| REQ-11 | Dados carregados e isolamento | registry UUID e DataManager por sessão | `test_uploads_are_isolated` | PASS |
| REQ-12 | Resposta correta | operações Pandas e contrato tipado | suítes `two-csv-real.spec.ts` e `real-data-assistant.spec.ts` | PASS |
| REQ-13 | Resposta em texto | campo `answer` na UI | E2E query real | PASS |
| REQ-14 | Resposta em tabela | `TableData` e `DataTable` | E2E agregação e listagem reais; screenshots 04 e 05 | PASS |
| REQ-15 | Resposta em gráfico | gráfico SVG derivado de tabela | E2E agregação real com SVG acessível; screenshot 04 | PASS |
| REQ-16 | Framework do curso | LangChain + Groq/Gemini | requirements/imports/relatório | PASS |

As suítes E2E reais iniciam FastAPI e Vite, fazem upload pelo navegador e não
usam mocks de resposta. Os artefatos de cada execução são temporários e ficam
em `frontend/test-results/`.
