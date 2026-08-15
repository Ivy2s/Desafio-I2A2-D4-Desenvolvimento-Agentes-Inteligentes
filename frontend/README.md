# Data Assistent frontend

Frontend independente para explorar datasets CSV e demonstrar consultas em linguagem natural. A UI não inicializa nem depende dos serviços Python.

## Stack

- React + TypeScript strict
- Vite
- ESLint
- Visualizações SVG próprias para gráficos de barras e linhas

```bash
npm install
npm run dev
npm run build
npm run lint
```

## Arquitetura

Os componentes conhecem somente os contratos em `src/contracts/` e recebem a implementação pela composição em `src/services/dataAssistantGateway.ts`:

```text
UI features -> DataAssistantGateway -> MockDataAssistantGateway
                             -> HttpDataAssistantGateway -> FastAPI
```

`MockDataAssistantGateway` é usado apenas durante o desenvolvimento da UI. Ele simula upload, processamento, latência, erros recuperáveis e cinco consultas de demonstração. O mock não representa processamento real e não usa LLM.

`HttpDataAssistantGateway` implementa upload, metadata, consulta e health sobre a API FastAPI. Ele pode ser instanciado com `new HttpDataAssistantGateway()` e usa `VITE_API_BASE_URL`, com default `http://127.0.0.1:8000`. O mock continua sendo o gateway padrão da aplicação nesta etapa. Nenhum `fetch()` está espalhado pelos componentes.

## Estrutura principal

- `src/app/`: composição da aplicação e estilos globais do shell
- `src/contracts/`: contratos de upload, dataset e consulta
- `src/features/upload/`: dropzone, etapas e estados de upload
- `src/features/dataset/`: resumo do dataset pronto
- `src/features/query/`: composer, sugestões, histórico, tabelas e gráficos
- `src/services/`: composição do gateway usado pela aplicação
- `src/mocks/`: fixtures determinísticas de desenvolvimento
