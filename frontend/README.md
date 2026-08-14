# Atlas frontend

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
```

`MockDataAssistantGateway` é usado apenas durante o desenvolvimento da UI. Ele simula upload, processamento, latência, erros recuperáveis e cinco consultas de demonstração. O mock não representa processamento real e não usa LLM.

O ponto futuro de integração é uma implementação `HttpDataAssistantGateway` no mesmo contrato. Nenhum `fetch()` está espalhado pelos componentes.

## Estrutura principal

- `src/app/`: composição da aplicação e estilos globais do shell
- `src/contracts/`: contratos de upload, dataset e consulta
- `src/features/upload/`: dropzone, etapas e estados de upload
- `src/features/dataset/`: resumo do dataset pronto
- `src/features/query/`: composer, sugestões, histórico, tabelas e gráficos
- `src/services/`: composição do gateway usado pela aplicação
- `src/mocks/`: fixtures determinísticas de desenvolvimento
